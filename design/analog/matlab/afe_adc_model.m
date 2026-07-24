function [y, metrics] = afe_adc_model(t, v_ecg_diff, p, filt)
%AFE_ADC_MODEL  MATLAB validation model for schematic-level AFE+ADC.
%
% Signal flow:
%   differential ECG
%   -> HPF
%   -> IA gain x201
%   -> 60 Hz notch
%   -> LPF
%   -> saturation to ADC input range
%   -> 12-bit offset-binary ADC
%   -> signed 12-bit stream

    y.time_s = t(:);
    y.v_diff = v_ecg_diff(:);

    % 1) HPF baseline removal
    y.v_hpf = filter(filt.b_hpf, filt.a_hpf, y.v_diff);

    % 2) IA gain
    y.v_ia = p.Av_total * y.v_hpf;

    % 3) 60 Hz notch
    y.v_notch = filter(filt.b_notch, filt.a_notch, y.v_ia);

    % 4) LPF anti-aliasing
    y.v_lpf = filter(filt.b_lpf, filt.a_lpf, y.v_notch);

    % 5) ADC input saturation
    y.v_adc_in = min(max(y.v_lpf, p.vref_n), p.vref_p);

    % 6) 12-bit offset-binary ADC
    y.adc_code = floor(((y.v_adc_in - p.vref_n) / (p.vref_p - p.vref_n)) * p.adc_max);
    y.adc_code = min(max(y.adc_code, 0), p.adc_max);

    % 7) signed stream for digital classifier, if needed
    y.adc_signed = y.adc_code - 2^(p.adc_bits - 1);

    % Metrics
    clip_hi = sum(y.v_lpf >= p.vref_p);
    clip_lo = sum(y.v_lpf <= p.vref_n);
    clip_ratio = 100 * (clip_hi + clip_lo) / length(y.v_lpf);

    metrics = table( ...
        max(abs(y.v_diff)), max(abs(y.v_hpf)), max(abs(y.v_ia)), ...
        max(abs(y.v_notch)), max(abs(y.v_lpf)), ...
        clip_hi, clip_lo, clip_ratio, ...
        min(y.adc_code), max(y.adc_code), max(y.adc_code)-min(y.adc_code), ...
        'VariableNames', { ...
        'InputDiffPeak_V', 'HPFPeak_V', 'IAPeak_V', 'NotchOutPeak_V', ...
        'AFEOutPeak_V', 'ClipHighCount', 'ClipLowCount', ...
        'ClipRatio_percent', 'ADCMin', 'ADCMax', 'ADCPeakToPeak'});
end
