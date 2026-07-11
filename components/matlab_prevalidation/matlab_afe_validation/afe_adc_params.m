function p = afe_adc_params()
%AFE_ADC_PARAMS  Schematic-derived AFE+ADC parameter set.
%
% Report flow:
%   Analog schematic values -> MATLAB validation -> SystemVerilog XModel
%
% This file keeps all values in one place so the report can clearly say
% that the MATLAB validation used the same schematic-level parameters.

    %% Sampling / ADC
    p.fs       = 1000;      % ADC sampling rate [Hz]
    p.adc_bits = 12;
    p.vref_n   = -1.65;     % ADC negative reference [V]
    p.vref_p   =  1.65;     % ADC positive reference [V]
    p.adc_max  = 2^p.adc_bits - 1;

    %% HPF: C=33nF, R=10Mohm
    p.R_hpf  = 10e6;
    p.C_hpf  = 33e-9;
    p.fc_hpf = 1/(2*pi*p.R_hpf*p.C_hpf);

    %% Instrumentation amplifier
    p.Rfb      = 100e3;
    p.Rg       = 1e3;
    p.Av_ia    = 1 + 2*p.Rfb/p.Rg;
    p.Av_diff  = 1;
    p.Av_total = p.Av_ia * p.Av_diff;

    %% Active Twin-T notch
    % Base Twin-T values: f0 ~= 1/(2*pi*R*C)
    p.f_notch = 60;
    p.R_twin  = 26.526e3;
    p.C_twin  = 100e-9;

    % Bootstrap gain k = Rk2/(Rk1+Rk2)
    p.Rk1 = 5e3;
    p.Rk2 = 95e3;
    p.k_boot  = p.Rk2/(p.Rk1 + p.Rk2);
    p.Q_notch = 1/(4*(1 - p.k_boot));

    %% LPF: R=1kohm, C=1.06uF
    p.R_lpf  = 1e3;
    p.C_lpf  = 1.06e-6;
    p.fc_lpf = 1/(2*pi*p.R_lpf*p.C_lpf);

    %% Op-amp behavioral assumptions used in XModel/schematic validation
    p.A_OL_dB = 100;
    p.CMRR_dB = 110;
end
