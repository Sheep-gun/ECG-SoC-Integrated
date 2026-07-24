function generate_prevalidation_reference_package()
%GENERATE_PREVALIDATION_REFERENCE_PACKAGE
% MATLAB 기반 ECG AFE+ADC nominal pre-validation reference package 생성.
%
% 목적:
%   - SystemVerilog XMODEL 구현 전 nominal parameter/frequency/headroom/code convention/reference vector 제공
%   - MATLAB-vs-XMODEL 비교용 golden/reference vector 생성
%
% 주의:
%   - transistor-level, PCB-level, silicon-level, clinical validation이 아님
%   - MATLAB과 XMODEL이 이미 bit-exact equivalent라는 claim이 아님
%   - afe_input_dataset/이 없으면 checked-in results_dataset/ artifact 기반 secondary report를 재생성함

    p = afe_adc_params();
    filt = design_afe_filters(p);

    results_dir = 'results_dataset';
    docs_dir    = 'docs';
    figures_dir = 'figures';
    ref_dir     = 'reference_vectors';

    ensure_dir(results_dir);
    ensure_dir(docs_dir);
    ensure_dir(figures_dir);
    ensure_dir(ref_dir);

    classes = {'NSR','CHF','ARR','AFF'};

    %% A. AFE+ADC parameter reference
    param_table = make_parameter_reference_table(p);
    writetable(param_table, fullfile(results_dir, 'afe_adc_parameter_reference.csv'));

    %% B. Frequency response numerical reference
    freq_table = make_frequency_response_metrics(p, filt);
    writetable(freq_table, fullfile(results_dir, 'afe_frequency_response_metrics.csv'));
    plot_total_frequency_response(p, filt, figures_dir);

    %% C. Dense 60 Hz active Twin-T notch reference
    [notch_table, notch_metrics] = make_notch_dense_sweep(p);
    writetable(notch_table, fullfile(results_dir, 'notch_dense_sweep.csv'));
    writetable(notch_metrics, fullfile(results_dir, 'notch_dense_sweep_metrics.csv'));
    plot_notch_dense_sweep(notch_table, notch_metrics, figures_dir);

    %% D. Dynamic range / ADC headroom reference
    headroom_table = make_dynamic_range_headroom_summary(classes, p, results_dir);
    writetable(headroom_table, fullfile(results_dir, 'afe_dynamic_range_headroom_summary.csv'));
    plot_dynamic_range_headroom(headroom_table, figures_dir);
    plot_adc_code_distribution(classes, results_dir, figures_dir);

    %% E. ADC code mapping convention
    mapping_table = make_adc_code_mapping_test(p);
    writetable(mapping_table, fullfile(results_dir, 'adc_code_mapping_test.csv'));

    %% F. Reference vector package and SHA256 manifest
    make_reference_vectors(classes, results_dir, ref_dir);
    normalize_reference_vector_line_endings(ref_dir);
    manifest_table = make_reference_vector_manifest(ref_dir);
    writetable(manifest_table, fullfile(ref_dir, 'reference_vector_manifest.csv'));
    write_reference_vector_manifest_md(manifest_table, fullfile(ref_dir, 'reference_vector_manifest.md'));
    normalize_reference_vector_line_endings(ref_dir);

    %% G. Input dataset manifest
    input_manifest = make_input_dataset_manifest(classes, ref_dir, p);
    writetable(input_manifest, fullfile(results_dir, 'input_dataset_manifest.csv'));

    %% H. Handoff/overview figures and docs
    plot_flow_figures(figures_dir);
    write_docs(docs_dir, figures_dir, param_table, freq_table, notch_metrics, headroom_table, mapping_table, input_manifest, p);

    fprintf('Generated MATLAB AFE+ADC nominal pre-validation reference package.\n');
end

%% ------------------------------------------------------------------------
function ensure_dir(d)
    if ~exist(d, 'dir')
        mkdir(d);
    end
end

function T = make_parameter_reference_table(p)
    block = {}; parameter = {}; value = {}; unit = {}; note = {};
    add('Sampling','fs',p.fs,'Hz','Nominal MATLAB/XMODEL stream sampling rate');
    add('HPF','R_hpf',p.R_hpf,'Ohm','Schematic-derived high-pass resistor');
    add('HPF','C_hpf',p.C_hpf,'F','Schematic-derived high-pass capacitor');
    add('HPF','fc_hpf',p.fc_hpf,'Hz','1/(2*pi*R*C), baseline drift reference');
    add('Instrumentation Amplifier','Rfb',p.Rfb,'Ohm','IA feedback resistor');
    add('Instrumentation Amplifier','Rg',p.Rg,'Ohm','IA gain-setting resistor');
    add('Instrumentation Amplifier','Av_ia',p.Av_ia,'V/V','1 + 2*Rfb/Rg');
    add('Differential Amplifier','Av_diff',p.Av_diff,'V/V','Unity differential stage in nominal model');
    add('Instrumentation Amplifier','Av_total',p.Av_total,'V/V','Av_ia * Av_diff');
    add('Notch','f_notch',p.f_notch,'Hz','60 Hz mains target');
    add('Notch','R_twin',p.R_twin,'Ohm','Active Twin-T nominal resistor');
    add('Notch','C_twin',p.C_twin,'F','Active Twin-T nominal capacitor reference');
    add('Notch','Rk1',p.Rk1,'Ohm','Bootstrap feedback resistor');
    add('Notch','Rk2',p.Rk2,'Ohm','Bootstrap feedback resistor');
    add('Notch','k_boot',p.k_boot,'V/V','Rk2/(Rk1+Rk2)');
    add('Notch','configured_Q',p.Q_notch,'-','Nominal configured Q = 1/(4*(1-k))');
    add('LPF','R_lpf',p.R_lpf,'Ohm','Schematic-derived low-pass resistor');
    add('LPF','C_lpf',p.C_lpf,'F','Schematic-derived low-pass capacitor');
    add('LPF','fc_lpf',p.fc_lpf,'Hz','1/(2*pi*R*C), anti-aliasing reference');
    add('ADC','adc_bits',p.adc_bits,'bit','Nominal ADC output width');
    add('ADC','vref_n',p.vref_n,'V','Negative ADC input reference');
    add('ADC','vref_p',p.vref_p,'V','Positive ADC input reference');
    add('ADC','adc_max',p.adc_max,'code','2^12 - 1');
    add('ADC','lsb',(p.vref_p-p.vref_n)/p.adc_max,'V/LSB','3.3/4095');
    add('Output stream','offset_binary_mem','%03X per line','hex','Physical ADC code reference; not canonical signed RTL replay format');
    add('Output stream','signed_decimal_txt','adc_offset_binary - 2048','decimal','Signed stream reference; final digital input contract is signed 12-bit ECG stream');
    add('Output stream','signed_twos_complement_mem','%03X per line','hex','Canonical downstream replay format: signed 12-bit two''s-complement hex .mem, encoded as mod(adc_signed,4096)');
    T = table(string(block(:)), string(parameter(:)), string(value(:)), string(unit(:)), string(note(:)), ...
        'VariableNames', {'block','parameter','value','unit','note'});

    function add(b, par, val, u, n)
        block{end+1} = b; %#ok<AGROW>
        parameter{end+1} = par; %#ok<AGROW>
        if isnumeric(val)
            value{end+1} = sprintf('%.12g', val); %#ok<AGROW>
        else
            value{end+1} = char(val); %#ok<AGROW>
        end
        unit{end+1} = u; %#ok<AGROW>
        note{end+1} = n; %#ok<AGROW>
    end
end

function T = make_frequency_response_metrics(p, filt)
    freq = [0.05; 0.1; p.fc_hpf; 1; 5; 10; 40; 50; 60; 100; 150; 250; 500];
    purpose = ["baseline drift region"; "low-frequency drift"; "HPF cutoff"; ...
        "ECG low-frequency passband"; "ECG main band"; "ECG main band"; ...
        "ECG morphology band"; "50 Hz mains reference"; "60 Hz notch target"; ...
        "high-frequency ECG/noise"; "LPF cutoff"; "pre-ADC high-frequency reference"; ...
        "1 kSPS Nyquist"];

    H = total_response(freq, p, filt);
    mag = abs(H);
    mag_db = 20*log10(max(mag, realmin));
    phase_deg = angle(H)*180/pi;

    interpretation_note = strings(numel(freq), 1);
    idx60 = abs(freq - 60) < 1e-9;
    if any(idx60)
        mag(idx60) = 0;
        mag_db(idx60) = -120;  % reporting cap for ideal digital zero
        interpretation_note(idx60) = "ideal digital notch zero; numerical dB value capped as < -120 dB; not a physical analog attenuation claim";
    end

    reference_passband_frequency_Hz = repmat(10.0, numel(freq), 1);
    idx10 = abs(freq - 10) < 1e-9;
    reference_passband_magnitude_dB = repmat(mag_db(idx10), numel(freq), 1);
    relative_to_10Hz_passband_dB = mag_db - reference_passband_magnitude_dB;

    passband_idx = abs(freq - 5) < 1e-9 | abs(freq - 10) < 1e-9 | abs(freq - 40) < 1e-9;
    passband_mean_magnitude_dB = repmat(mean(mag_db(passband_idx)), numel(freq), 1);
    passband_mean_frequency_range_Hz = repmat("5,10,40 nominal ECG passband reference points", numel(freq), 1);
    relative_to_passband_mean_dB = mag_db - passband_mean_magnitude_dB;
    relative_interpretation_note = repmat("absolute gain includes IA x201; relative columns show attenuation/amplification compared with ECG passband reference", numel(freq), 1);
    if any(idx60)
        relative_interpretation_note(idx60) = "60 Hz uses ideal digital notch reporting cap; relative values are capped and not physical analog attenuation claims";
    end

    group_delay_samples = nan(size(freq));
    for i = 1:numel(freq)
        f = freq(i);
        if f > 0.02 && f < p.fs/2 - 0.02 && abs(f - 60) > 0.05
            df = max(0.001, f*1e-4);
            fpair = [f-df, f+df];
            Hpair = total_response(fpair, p, filt);
            ph = unwrap(angle(Hpair));
            w = 2*pi*fpair/p.fs;
            group_delay_samples(i) = -(ph(2)-ph(1))/(w(2)-w(1));
        end
    end
    group_delay_ms = group_delay_samples / p.fs * 1000;
    model_note = repmat("digital MATLAB nominal chain: HPF*IA*digital Q≈5 notch*LPF", numel(freq), 1);

    T = table(freq, purpose, mag, mag_db, phase_deg, group_delay_samples, group_delay_ms, model_note, interpretation_note, ...
        reference_passband_frequency_Hz, reference_passband_magnitude_dB, relative_to_10Hz_passband_dB, ...
        passband_mean_frequency_range_Hz, passband_mean_magnitude_dB, relative_to_passband_mean_dB, relative_interpretation_note, ...
        'VariableNames', {'frequency_Hz','purpose','magnitude_V_per_V','magnitude_dB','phase_deg','group_delay_samples','group_delay_ms','model_note','interpretation_note', ...
        'reference_passband_frequency_Hz','reference_passband_magnitude_dB','relative_to_10Hz_passband_dB', ...
        'passband_mean_frequency_range_Hz','passband_mean_magnitude_dB','relative_to_passband_mean_dB','relative_interpretation_note'});
end

function H = total_response(f, p, filt)
    H = freqz_eval(filt.b_hpf, filt.a_hpf, f, p.fs) .* p.Av_total .* ...
        freqz_eval(filt.b_notch, filt.a_notch, f, p.fs) .* ...
        freqz_eval(filt.b_lpf, filt.a_lpf, f, p.fs);
end

function H = freqz_eval(b, a, f, fs)
    f = f(:);
    w = 2*pi*f/fs;
    zinv = exp(-1j*w);
    num = zeros(size(f)); den = zeros(size(f));
    for k = 1:numel(b)
        num = num + b(k) .* zinv.^(k-1);
    end
    for k = 1:numel(a)
        den = den + a(k) .* zinv.^(k-1);
    end
    H = num ./ den;
end

function [T, M] = make_notch_dense_sweep(p)
    frequency_Hz = (30:0.001:100)';
    H = active_twin_t_response(frequency_Hz, p.R_twin, p.C_twin, p.k_boot);
    magnitude_V_per_V = abs(H(:));
    magnitude_dB = 20*log10(max(magnitude_V_per_V, realmin));
    phase_deg = angle(H(:))*180/pi;
    T = table(frequency_Hz, magnitude_V_per_V, magnitude_dB, phase_deg);

    [min_att, idx] = min(magnitude_dB);
    center = frequency_Hz(idx);
    H60 = active_twin_t_response(60, p.R_twin, p.C_twin, p.k_boot);
    H50 = active_twin_t_response(50, p.R_twin, p.C_twin, p.k_boot);
    exact60 = 20*log10(max(abs(H60), realmin));
    att50 = 20*log10(max(abs(H50), realmin));

    % Local passband reference: use 30 Hz and 100 Hz sweep endpoints.
    local_ref = mean([magnitude_dB(1), magnitude_dB(end)]);
    threshold = local_ref - 3;
    mask = magnitude_dB <= threshold;
    if any(mask)
        idxs = find(mask);
        bw_low = frequency_Hz(idxs(1));
        bw_high = frequency_Hz(idxs(end));
        bw = bw_high - bw_low;
        q_est = center / bw;
    else
        bw_low = NaN; bw_high = NaN; bw = NaN; q_est = NaN;
    end

    M = table(60, 30, 100, center, exact60, min_att, local_ref, threshold, bw_low, bw_high, bw, q_est, p.Q_notch, att50, ...
        "No; nominal MATLAB reference only", ...
        "Bandwidth is computed relative to the local passband reference magnitude from 30 Hz and 100 Hz endpoints. Estimated Q is a nominal sweep estimate, not a measured physical circuit Q.", ...
        "60 Hz mains target; not claimed as complete 50 Hz rejection", ...
        'VariableNames', {'target_frequency_Hz','sweep_low_Hz','sweep_high_Hz','notch_center_frequency_Hz','exact_60Hz_attenuation_dB', ...
        'minimum_attenuation_dB_in_sweep','local_passband_reference_dB','minus3dB_threshold_dB','bandwidth_low_Hz','bandwidth_high_Hz', ...
        'bandwidth_Hz','estimated_Q_from_sweep','configured_Q','attenuation_at_50Hz_dB','physical_Q_claim','definition_note','scope_note'});
end

function T = make_dynamic_range_headroom_summary(classes, p, results_dir)
    rows = table();
    lsb = (p.vref_p - p.vref_n) / p.adc_max;
    for i = 1:numel(classes)
        rec = classes{i};
        f = fullfile(results_dir, rec, 'matlab_afe_adc_output.csv');
        if ~exist(f, 'file')
            warning('Missing %s', f);
            continue;
        end
        D = readtable(f);
        duration = D.time_s(end) - D.time_s(1) + 1/p.fs;
        afe_min = min(D.v_lpf); afe_max = max(D.v_lpf);
        adc_min_v = min(D.v_adc_in); adc_max_v = max(D.v_adc_in);
        code_min = min(D.adc_code); code_max = max(D.adc_code);
        pos_hits = sum(D.v_lpf >= p.vref_p);
        neg_hits = sum(D.v_lpf <= p.vref_n);
        clip_ratio = 100*(pos_hits+neg_hits)/height(D);
        pos_headroom = p.vref_p - adc_max_v;
        neg_headroom = adc_min_v - p.vref_n;
        min_headroom = min(pos_headroom, neg_headroom);

        R = table(string(rec), duration, height(D), p.fs, afe_min, afe_max, adc_min_v, adc_max_v, ...
            code_min, code_max, code_max-code_min, pos_hits, neg_hits, clip_ratio, ...
            pos_headroom, neg_headroom, min_headroom, min_headroom/lsb, ...
            'VariableNames', {'record_name','input_duration_s','sample_count','sampling_rate_Hz', ...
            'afe_output_min_V','afe_output_max_V','adc_input_min_V','adc_input_max_V','adc_code_min','adc_code_max', ...
            'adc_code_peak_to_peak','positive_rail_hit_count','negative_rail_hit_count','clipping_ratio_percent', ...
            'positive_headroom_to_rail_V','negative_headroom_to_rail_V','minimum_headroom_to_rail_V','minimum_headroom_to_rail_LSB'});
        rows = [rows; R]; %#ok<AGROW>
    end
    T = rows;
end

function T = make_adc_code_mapping_test(p)
    lsb = (p.vref_p - p.vref_n) / p.adc_max;
    vin = [p.vref_n; -1; -lsb; 0; lsb; 1; p.vref_p];
    code = floor(((vin - p.vref_n)/(p.vref_p-p.vref_n))*p.adc_max);
    code = min(max(code, 0), p.adc_max);
    signed = code - 2^(p.adc_bits-1);

    offset_hex = strings(numel(code),1);
    signed_twos_hex = strings(numel(code),1);
    for i = 1:numel(code)
        offset_hex(i) = upper(dec2hex(code(i), 3));
        signed_twos_hex(i) = upper(dec2hex(mod(signed(i), 4096), 3));
    end

    formula = repmat("floor((V + 1.65)/3.3 * 4095), clipped to [0,4095]", numel(code), 1);
    signed_formula = repmat("signed_decimal = offset_binary - 2048; signed_twos_complement_hex = dec2hex(mod(signed_decimal,4096),3)", numel(code), 1);
    note = strings(numel(code), 1);
    note(vin == p.vref_n) = "negative full-scale";
    note(vin == 0) = "0 V maps to offset-binary 2047 and signed -1 because floor() is used";
    note(vin == p.vref_p) = "positive full-scale";

    T = table(vin, code, offset_hex, signed, signed_twos_hex, formula, signed_formula, note, ...
        'VariableNames', {'input_voltage_V','offset_binary_code_decimal','offset_binary_code_hex','signed_decimal','signed_twos_complement_hex','formula','signed_conversion_formula','note'});
end

function make_reference_vectors(classes, results_dir, ref_dir)
    ensure_dir(ref_dir);
    for i = 1:numel(classes)
        rec = classes{i};
        out_dir = fullfile(ref_dir, rec);
        ensure_dir(out_dir);
        src_csv = fullfile(results_dir, rec, 'matlab_afe_adc_output.csv');
        if ~exist(src_csv, 'file')
            error('make_reference_vectors:MissingStageOutput', ...
                  'Required stage output missing: %s', src_csv);
        end

        D = readtable(src_csv);
        assert_required_vector_table(D, rec);

        sample_index = (0:height(D)-1)';
        time_s = D.time_s;
        voltage_V = D.v_diff;
        source_code_signed_est_5uV_per_code = round(voltage_V * 200000);
        inputT = table(sample_index, time_s, voltage_V, source_code_signed_est_5uV_per_code);
        writetable(inputT, fullfile(out_dir, 'input.csv'));

        if any(strcmp(D.Properties.VariableNames, 'adc_code'))
            D.Properties.VariableNames{strcmp(D.Properties.VariableNames, 'adc_code')} = 'adc_offset_binary';
        end
        writetable(D, fullfile(out_dir, 'matlab_stage_outputs.csv'));

        src_ob = fullfile(results_dir, rec, 'matlab_adc_offset_binary_hex.mem');
        src_sd = fullfile(results_dir, rec, 'matlab_adc_signed_decimal.txt');
        if ~exist(src_ob, 'file') || ~exist(src_sd, 'file')
            error('make_reference_vectors:MissingAdcOutput', ...
                  'Required ADC output files missing for %s', rec);
        end
        copyfile(src_ob, fullfile(out_dir, 'adc_offset_binary.mem'));
        copyfile(src_sd, fullfile(out_dir, 'adc_signed.txt'));

        adc_signed = D.adc_signed;
        write_signed_twos_complement_mem(fullfile(out_dir, 'adc_signed_twos_complement.mem'), adc_signed);
    end

    validate_required_reference_vectors(ref_dir, classes);
end


function assert_required_vector_table(D, rec)
    required_vars = {'time_s','v_diff','v_hpf','v_ia','v_notch','v_lpf','v_adc_in','adc_signed'};
    for k = 1:numel(required_vars)
        if ~any(strcmp(D.Properties.VariableNames, required_vars{k}))
            error('assert_required_vector_table:MissingColumn', ...
                  '%s missing required column %s', rec, required_vars{k});
        end
    end
    if any(strcmp(D.Properties.VariableNames, 'adc_offset_binary'))
        adc_col = 'adc_offset_binary';
    elseif any(strcmp(D.Properties.VariableNames, 'adc_code'))
        adc_col = 'adc_code';
    else
        error('assert_required_vector_table:MissingAdcCode', ...
              '%s missing adc_offset_binary/adc_code column', rec);
    end
    if height(D) ~= 60000
        error('assert_required_vector_table:BadSampleCount', ...
              '%s must have 60000 samples, got %d', rec, height(D));
    end
    dt = median(diff(D.time_s));
    fs_est = 1/dt;
    if abs(fs_est - 1000) > 1e-6
        error('assert_required_vector_table:BadSamplingRate', ...
              '%s must be 1 kSPS, got %.9g Hz', rec, fs_est);
    end
    if any(~isfinite(D.(adc_col))) || any(~isfinite(D.adc_signed))
        error('assert_required_vector_table:NonFiniteAdc', ...
              '%s has non-finite ADC output values', rec);
    end
end

function write_signed_twos_complement_mem(out_file, adc_signed)
    adc_signed = double(adc_signed(:));
    if numel(adc_signed) ~= 60000
        error('write_signed_twos_complement_mem:BadLength', ...
              'signed two''s-complement .mem requires 60000 samples, got %d', numel(adc_signed));
    end
    encoded = mod(adc_signed, 4096);
    fid = fopen(out_file, 'wb');
    if fid < 0
        error('write_signed_twos_complement_mem:OpenFailed', 'Cannot open %s', out_file);
    end
    cleaner = onCleanup(@() fclose(fid));
    for ii = 1:numel(encoded)
        fwrite(fid, sprintf('%03X', encoded(ii)), 'char');
        fwrite(fid, uint8(10), 'uint8'); % force LF byte even on Windows
    end
end

function validate_required_reference_vectors(ref_dir, classes)
    required_files = {'input.csv','matlab_stage_outputs.csv','adc_offset_binary.mem','adc_signed.txt','adc_signed_twos_complement.mem'};
    for i = 1:numel(classes)
        rec = classes{i};
        for k = 1:numel(required_files)
            f = fullfile(ref_dir, rec, required_files{k});
            if ~exist(f, 'file')
                error('validate_required_reference_vectors:MissingFile', ...
                      'Required reference vector missing: %s', f);
            end
        end
    end
end



function normalize_reference_vector_line_endings(ref_dir)
    % Ensure hash-target reference text files use LF bytes before SHA256.
    exts = {'.csv','.txt','.mem','.md'};
    files = dir(fullfile(ref_dir, '**', '*'));
    for i = 1:numel(files)
        if files(i).isdir
            continue;
        end
        [~,~,ext] = fileparts(files(i).name);
        if ~any(strcmpi(ext, exts))
            continue;
        end
        full = fullfile(files(i).folder, files(i).name);
        fid = fopen(full, 'rb');
        if fid < 0
            error('normalize_reference_vector_line_endings:OpenFailed', 'Cannot open %s', full);
        end
        data = fread(fid, Inf, '*uint8');
        fclose(fid);
        data = uint8(data(:).');
        data = strrep(char(data), sprintf('\r\n'), sprintf('\n'));
        data = strrep(data, sprintf('\r'), sprintf('\n'));
        fid = fopen(full, 'wb');
        if fid < 0
            error('normalize_reference_vector_line_endings:OpenFailed', 'Cannot write %s', full);
        end
        fwrite(fid, unicode2native(data, 'UTF-8'), 'uint8');
        fclose(fid);
    end
end

function T = make_reference_vector_manifest(ref_dir)
    % Build a path-portable manifest for reference_vectors/.
    % MATLAB on Windows may return absolute paths such as an absolute Windows user path in
    % dir().folder.  For GitHub/XMODEL handoff, the manifest must always
    % use repository-relative paths:
    %   reference_vectors/<CLASS>/<FILE>
    files = dir(fullfile(ref_dir, '**', '*'));
    rel = {}; cls = {}; role = {}; bytes = []; sha = {};

    for i = 1:numel(files)
        if files(i).isdir || contains(files(i).name, 'reference_vector_manifest')
            continue;
        end

        full = fullfile(files(i).folder, files(i).name);
        norm_full = strrep(full, '\', '/');
        marker = '/reference_vectors/';
        idx = strfind(norm_full, marker);

        if ~isempty(idx)
            % Keep only <CLASS>/<FILE> after the last reference_vectors marker.
            r = norm_full(idx(end) + length(marker):end);
        else
            % Fallback for relative folder strings.
            norm_ref = strrep(ref_dir, '\', '/');
            r = strrep(norm_full, [norm_ref '/'], '');
        end

        r = regexprep(r, '^/+|/+$', '');
        parts = split(string(r), '/');

        rel{end+1,1} = ['reference_vectors/' char(r)]; %#ok<AGROW>
        if numel(parts) >= 2
            cls{end+1,1} = char(parts(1)); %#ok<AGROW>
        else
            cls{end+1,1} = ''; %#ok<AGROW>
        end
        role{end+1,1} = files(i).name; %#ok<AGROW>
        bytes(end+1,1) = files(i).bytes; %#ok<AGROW>
        sha{end+1,1} = sha256_file(full); %#ok<AGROW>
    end

    T = table(string(rel), string(cls), string(role), bytes, string(sha), ...
        'VariableNames', {'relative_path','class','file_role','bytes','sha256'});
end

function write_reference_vector_manifest_md(T, out_file)
    lines = {};
    lines{end+1} = '# Reference Vector Manifest';
    lines{end+1} = '';
    lines{end+1} = '이 문서는 MATLAB reference input/output vector의 SHA256 hash를 정리한다. 이 vector는 후속 MATLAB-vs-XMODEL equivalence verification의 기준으로 사용된다.';
    lines{end+1} = '';
    lines{end+1} = '> `source_code_signed_est_5uV_per_code`는 원본 ECG 입력 전압 scale 추적용 estimate이며 AFE ADC output code가 아니다. XMODEL analog input은 `voltage_V`를 사용한다.';
    lines{end+1} = '';
    lines{end+1} = '## Output format 구분';
    lines{end+1} = '';
    lines{end+1} = '- `adc_offset_binary.mem`: physical ADC offset-binary code convention 확인용 reference이다.';
    lines{end+1} = '- `adc_signed.txt`: offset-binary code에서 mid-code 2048을 제거한 signed decimal stream reference이다.';
    lines{end+1} = '- `adc_signed_twos_complement.mem`: 공식 downstream canonical replay format이다. signed 12-bit stream을 12-bit two''s-complement bit pattern으로 encoding한 3자리 대문자 hex `.mem`이며, 한 줄당 1 sample을 저장한다.';
    lines{end+1} = '- `adc_signed_twos_complement.mem`의 각 줄은 `encoded = mod(adc_signed, 4096)`와 동일하다.';
    lines{end+1} = '';
    lines{end+1} = '## Manifest';
    lines{end+1} = '';
    lines{end+1} = '| Class | File role | Relative path | Bytes | SHA256 |';
    lines{end+1} = '|---|---|---|---:|---|';
    for i = 1:height(T)
        lines{end+1} = sprintf('| %s | %s | `%s` | %d | `%s` |', T.class(i), T.file_role(i), T.relative_path(i), T.bytes(i), T.sha256(i)); %#ok<AGROW>
    end
    write_text(out_file, strjoin(lines, newline));
end

function T = make_input_dataset_manifest(classes, ref_dir, p)
    input_class = strings(numel(classes),1);
    source_database = strings(numel(classes),1);
    source_record_id = strings(numel(classes),1);
    source_segment_start_s = strings(numel(classes),1);
    source_segment_duration_s = zeros(numel(classes),1);
    source_selection_note = strings(numel(classes),1);
    source_traceability_status = strings(numel(classes),1);
    expected_input_path = strings(numel(classes),1);
    raw_source_file_in_repo = strings(numel(classes),1);
    raw_source_input_sha256 = strings(numel(classes),1);
    checked_in_reference_input_path = strings(numel(classes),1);
    checked_in_reference_input_sha256 = strings(numel(classes),1);
    sample_count = zeros(numel(classes),1);
    sampling_rate_Hz = zeros(numel(classes),1);
    duration_s = zeros(numel(classes),1);
    voltage_min_V = zeros(numel(classes),1);
    voltage_max_V = zeros(numel(classes),1);
    checked_in_reference_copy_in_repo = strings(numel(classes),1);
    regeneration_method = strings(numel(classes),1);

    for i = 1:numel(classes)
        rec = classes{i};
        input_class(i) = string(rec);
        switch rec
            case 'NSR'
                source_database(i) = "nsrdb";
                source_record_id(i) = "16539";
                source_selection_note(i) = "nominal headroom/reference-vector 검증용 대표 NSR 입력; upstream dataset flow에서 생성됨; exact segment start는 이 MATLAB repo에서 추적하지 않음";
            case 'CHF'
                source_database(i) = "chfdb";
                source_record_id(i) = "chf05";
                source_selection_note(i) = "nominal headroom/reference-vector 검증용 대표 CHF 입력; upstream dataset flow에서 생성됨; exact segment start는 이 MATLAB repo에서 추적하지 않음";
            case 'ARR'
                source_database(i) = "mitdb";
                source_record_id(i) = "105";
                source_selection_note(i) = "nominal headroom/reference-vector 검증용 대표 ARR 입력; upstream dataset flow에서 생성됨; exact segment start는 이 MATLAB repo에서 추적하지 않음";
            case 'AFF'
                source_database(i) = "afdb";
                source_record_id(i) = "04015";
                source_selection_note(i) = "nominal headroom/reference-vector 검증용 대표 AFF 입력; upstream dataset flow에서 생성됨; exact segment start는 이 MATLAB repo에서 추적하지 않음";
            otherwise
                source_database(i) = "not tracked";
                source_record_id(i) = "not tracked";
                source_selection_note(i) = "not tracked in this MATLAB repo; checked-in reference input and SHA256 are provided";
        end
        source_segment_start_s(i) = "not tracked in this MATLAB repo; checked-in reference input and SHA256 are provided";
        source_segment_duration_s(i) = 60.0;
        source_traceability_status(i) = "partial: source database/record tracked; exact segment start not tracked in this MATLAB repo; checked-in reference input and SHA256 are provided";
        expected_input_path(i) = "afe_input_dataset/afe_input_" + string(rec) + ".csv";
        raw_path = char(expected_input_path(i));
        if exist(raw_path, 'file')
            raw_source_file_in_repo(i) = "Yes";
            raw_source_input_sha256(i) = string(sha256_file(raw_path));
        else
            raw_source_file_in_repo(i) = "No";
            raw_source_input_sha256(i) = "N/A; raw source input not checked in";
        end
        ref_path = fullfile(ref_dir, rec, 'input.csv');
        checked_in_reference_input_path(i) = "reference_vectors/" + string(rec) + "/input.csv";
        if exist(ref_path, 'file')
            checked_in_reference_copy_in_repo(i) = "Yes";
            checked_in_reference_input_sha256(i) = string(sha256_file(ref_path));
            D = readtable(ref_path);
            sample_count(i) = height(D);
            sampling_rate_Hz(i) = p.fs;
            duration_s(i) = height(D)/p.fs;
            source_segment_duration_s(i) = duration_s(i);
            voltage_min_V(i) = min(D.voltage_V);
            voltage_max_V(i) = max(D.voltage_V);
        else
            checked_in_reference_copy_in_repo(i) = "No";
            checked_in_reference_input_sha256(i) = "N/A";
            sample_count(i) = NaN;
            sampling_rate_Hz(i) = p.fs;
            duration_s(i) = NaN;
            source_segment_duration_s(i) = NaN;
            voltage_min_V(i) = NaN;
            voltage_max_V(i) = NaN;
        end
        regeneration_method(i) = "Full regeneration requires afe_input_dataset/; without it, rebuild secondary reports/figures/manifests from checked-in results_dataset artifacts.";
    end

    T = table(input_class, source_database, source_record_id, source_segment_start_s, source_segment_duration_s, ...
        source_selection_note, source_traceability_status, expected_input_path, raw_source_file_in_repo, raw_source_input_sha256, ...
        checked_in_reference_input_path, checked_in_reference_input_sha256, ...
        sample_count, sampling_rate_Hz, duration_s, voltage_min_V, voltage_max_V, ...
        checked_in_reference_copy_in_repo, regeneration_method);
end

function h = sha256_file(filename)
    fid = fopen(filename, 'r');
    data = fread(fid, Inf, '*uint8');
    fclose(fid);
    md = java.security.MessageDigest.getInstance('SHA-256');
    md.update(data);
    hash = typecast(md.digest(), 'uint8');
    h = lower(reshape(dec2hex(hash)', 1, []));
end

%% Plot functions ----------------------------------------------------------
function plot_total_frequency_response(p, filt, figures_dir)
    % Layout note:
    % Avoid xline label overlap by drawing vertical reference lines and
    % placing labels at separate y positions.
    f = logspace(log10(0.03), log10(500), 4000);
    [~,Hh] = freq_response_discrete(filt.b_hpf,   filt.a_hpf,   p.fs, f);
    [~,Hn] = freq_response_discrete(filt.b_notch, filt.a_notch, p.fs, f);
    [~,Hl] = freq_response_discrete(filt.b_lpf,   filt.a_lpf,   p.fs, f);
    H = p.Av_total .* Hh .* Hn .* Hl;
    mag_db = 20*log10(max(abs(H), 1e-6));

    fig = figure('Visible','off', 'Position', [100 100 1500 720]);
    semilogx(f, mag_db, 'LineWidth', 1.3); grid on; hold on;
    xlabel('Frequency [Hz]');
    ylabel('Magnitude [dB]');
    title('MATLAB Nominal AFE+ADC Frequency Response Reference');

    ylim([-125, 55]);
    xlim([0.03, 500]);

    xline(p.fc_hpf, '--', 'Color', [0.45 0.45 0.45]);
    xline(60, '--', 'Color', [0.45 0.45 0.45]);
    xline(p.fc_lpf, '--', 'Color', [0.45 0.45 0.45]);

    text(p.fc_hpf*1.10, -112, sprintf('HPF cutoff\n0.482 Hz'), ...
         'FontSize', 8, 'HorizontalAlignment','left', 'VerticalAlignment','middle', ...
         'BackgroundColor','w', 'Margin', 3);
    text(60*1.05, -78, sprintf('60 Hz digital\nnotch target'), ...
         'FontSize', 8, 'HorizontalAlignment','left', 'VerticalAlignment','middle', ...
         'BackgroundColor','w', 'Margin', 3);
    text(p.fc_lpf*1.04, -98, sprintf('LPF cutoff\n150 Hz'), ...
         'FontSize', 8, 'HorizontalAlignment','left', 'VerticalAlignment','middle', ...
         'BackgroundColor','w', 'Margin', 3);

    note = sprintf(['60 Hz may be an ideal digital notch zero in the time-domain model.\n', ...
                    'Use active Twin-T dense sweep for analog-style notch attenuation claim.']);
    text(0.965, 0.18, note, 'Units','normalized', ...
         'HorizontalAlignment','right', 'VerticalAlignment','bottom', ...
         'FontSize', 8, 'BackgroundColor','w', 'EdgeColor',[0.6 0.6 0.6], 'Margin', 6);

    save_figure(fig, figures_dir, 'fig_total_frequency_response');
end

function plot_notch_dense_sweep(T, M, figures_dir)
    fig = figure('Visible','off');
    plot(T.frequency_Hz, T.magnitude_dB); grid on;
    xlabel('Frequency [Hz]'); ylabel('Magnitude [dB]');
    title('Dense 60 Hz Active Twin-T Notch Reference');
    xline(60, '--', '60 Hz target');
    yline(M.minus3dB_threshold_dB(1), ':', 'local passband -3 dB');
    txt = sprintf('60 Hz attenuation %.2f dB; configured Q %.1f; estimated Q %.2f', ...
        M.exact_60Hz_attenuation_dB(1), M.configured_Q(1), M.estimated_Q_from_sweep(1));
    text(35, -70, txt, 'FontSize', 8);
    save_figure(fig, figures_dir, 'fig_notch_dense_sweep');
end

function plot_dynamic_range_headroom(T, figures_dir)
    fig = figure('Visible','off');
    bar(categorical(T.record_name), T.minimum_headroom_to_rail_V); grid on;
    ylabel('Minimum headroom to ADC rail [V]');
    title('ADC Headroom Reference for Representative ECG Inputs');
    save_figure(fig, figures_dir, 'fig_dynamic_range_headroom');
end

function plot_adc_code_distribution(classes, results_dir, figures_dir)
    fig = figure('Visible','off'); hold on; grid on;
    for i = 1:numel(classes)
        D = readtable(fullfile(results_dir, classes{i}, 'matlab_afe_adc_output.csv'));
        if any(strcmp(D.Properties.VariableNames,'adc_code'))
            codes = D.adc_code;
        else
            codes = D.adc_offset_binary;
        end
        histogram(codes, 80, 'Normalization', 'pdf', 'DisplayStyle', 'stairs');
    end
    xline(0, '--'); xline(2048, ':'); xline(4095, '--');
    legend(classes, 'Location', 'best');
    xlabel('Offset-binary ADC code'); ylabel('Density');
    title('ADC Code Distribution Reference');
    save_figure(fig, figures_dir, 'fig_adc_code_distribution');
end

function plot_flow_figures(figures_dir)
    simple_flow({'MATLAB nominal pre-validation','SystemVerilog XMODEL AFE+ADC','Digital SNN RTL / Vivado / Vitis','XMODEL stream + locked RTL'}, ...
        'AFE+ADC Validation Role in Project Flow', figures_dir, 'fig_matlab_prevalidation_flow');
    simple_flow({'ECG input','HPF 0.482 Hz','IA x201','60 Hz notch','LPF 150 Hz','12-bit ADC'}, ...
        'MATLAB Nominal AFE+ADC Chain Overview', figures_dir, 'fig_afe_chain_overview');
    simple_flow({'Representative ECG input','MATLAB stage outputs','Reference vectors + SHA256 manifest','XMODEL / RTL replay using signed two''s-complement .mem'}, ...
        'MATLAB Reference Vector Handoff Flow', figures_dir, 'fig_reference_vector_handoff');
end

function simple_flow(labels, ttl, figures_dir, name)
    % Use figure-normalized annotation boxes and arrows so text and arrows
    % stay in the same coordinate system. This avoids overlap when exported
    % to PNG/PDF across MATLAB versions.
    fig = figure('Visible','off', 'Position', [100 100 1700 720]);
    clf(fig);
    annotation('textbox', [0.05 0.90 0.90 0.06], 'String', ttl, ...
        'EdgeColor','none', 'HorizontalAlignment','center', ...
        'VerticalAlignment','middle', 'FontSize', 14, 'FontWeight','bold');

    n = numel(labels);
    left_margin = 0.07;
    right_margin = 0.07;
    gap = 0.035;
    box_w = (1 - left_margin - right_margin - gap*(n-1)) / n;
    box_h = 0.25;
    y = 0.43;

    for i = 1:n
        x = left_margin + (i-1)*(box_w + gap);
        label = wrap_label(labels{i}, 20);
        annotation('textbox', [x, y, box_w, box_h], ...
            'String', label, 'FitBoxToText','off', ...
            'HorizontalAlignment','center', 'VerticalAlignment','middle', ...
            'FontSize', 8.5, 'LineWidth', 1.1, ...
            'BackgroundColor','w', 'Margin', 6);

        if i < n
            x1 = x + box_w + 0.006;
            x2 = x + box_w + gap - 0.006;
            ymid = y + box_h/2;
            annotation('arrow', [x1 x2], [ymid ymid], 'LineWidth', 1.1);
        end
    end

    annotation('textbox', [0.12 0.13 0.76 0.07], ...
        'String', 'MATLAB nominal reference only; not transistor/PCB/silicon validation or MATLAB-vs-XMODEL bit-exact equivalence.', ...
        'EdgeColor','none', 'HorizontalAlignment','center', ...
        'VerticalAlignment','middle', 'FontSize', 8, 'FontAngle','italic');

    save_figure(fig, figures_dir, name);
end

function out = wrap_label(in, width)
    words = split(string(in));
    out = "";
    line = "";
    for k = 1:numel(words)
        w = words(k);
        if strlength(line) == 0
            line = w;
        elseif strlength(line) + 1 + strlength(w) <= width
            line = line + " " + w;
        else
            if strlength(out) == 0
                out = line;
            else
                out = out + newline + line;
            end
            line = w;
        end
    end
    if strlength(line) > 0
        if strlength(out) == 0
            out = line;
        else
            out = out + newline + line;
        end
    end
    out = char(out);
end

function save_figure(fig, figures_dir, name)
    ensure_dir(figures_dir);
    saveas(fig, fullfile(figures_dir, [name '.png']));
    saveas(fig, fullfile(figures_dir, [name '.pdf']));
    close(fig);
end

%% Docs -------------------------------------------------------------------
function write_docs(docs_dir, figures_dir, param_table, freq_table, notch_metrics, headroom_table, mapping_table, input_manifest, p)
    write_text(fullfile(docs_dir, 'afe_adc_parameter_reference.md'), compose_parameter_doc(param_table));
    write_text(fullfile(docs_dir, 'frequency_response_reference.md'), compose_frequency_doc(freq_table));
    write_text(fullfile(docs_dir, 'notch_60hz_reference.md'), compose_notch_doc(notch_metrics));
    write_text(fullfile(docs_dir, 'dynamic_range_headroom_reference.md'), compose_headroom_doc(headroom_table));
    write_text(fullfile(docs_dir, 'adc_code_mapping_convention.md'), compose_adc_mapping_doc(mapping_table));
    write_text(fullfile(docs_dir, 'MATLAB_TO_XMODEL_HANDOFF.md'), compose_handoff_doc(p));
    write_text(fullfile(docs_dir, 'INPUT_DATASET_MANIFEST.md'), compose_input_manifest_doc(input_manifest));
    write_text(fullfile(docs_dir, 'VALIDATION_STATUS.md'), compose_validation_status_doc());
    write_text(fullfile(figures_dir, 'FIGURE_CAPTIONS.md'), compose_figure_captions_doc());
end

function write_text(file, txt)
    % Write generated text with explicit LF bytes for reproducible SHA256
    % across Windows/macOS/Linux.
    if isstring(txt)
        txt = char(txt);
    end
    txt = strrep(txt, sprintf('\r\n'), sprintf('\n'));
    txt = strrep(txt, sprintf('\r'), sprintf('\n'));

    fid = fopen(file, 'wb');
    if fid < 0
        error('write_text:OpenFailed', 'Cannot open %s', file);
    end
    cleaner = onCleanup(@() fclose(fid));
    fwrite(fid, unicode2native(txt, 'UTF-8'), 'uint8');
end

function s = compose_parameter_doc(T)
    lines = {
        '# AFE+ADC Parameter Reference'
        ''
        '이 문서는 XMODEL 구현자가 그대로 참고할 nominal AFE+ADC parameter reference이다.'
        '실제 transistor-level 또는 post-layout 검증 완료를 의미하지 않는다.'
        ''
    };
    s = [strjoin(lines, newline), newline, table_to_md(T)];
end

function s = compose_frequency_doc(T)
    lines = {
        '# Frequency Response Numerical Reference'
        ''
        'CSV: `results_dataset/afe_frequency_response_metrics.csv`'
        ''
        '본 결과는 XMODEL 구현 전 MATLAB reference frequency response이다. absolute magnitude는 IA gain ×201을 포함한 전체 MATLAB nominal chain gain이다. 따라서 0.05 Hz 같은 baseline-drift 영역에서도 absolute dB 값이 양수로 보일 수 있다. 해석에는 `relative_to_10Hz_passband_dB` 또는 `relative_to_passband_mean_dB` column을 함께 사용한다.'
        ''
        'MATLAB time-domain chain의 60 Hz digital notch approximation은 정확히 60 Hz에서 ideal zero를 만들 수 있다. 따라서 60 Hz의 numerical dB 값은 physical analog attenuation claim이 아니며, CSV에서는 `< -120 dB` reporting cap으로 해석한다. 최종 논문에서 사용할 analog-style notch attenuation claim은 active Twin-T dense sweep 결과를 사용한다.'
        ''
    };
    s = [strjoin(lines, newline), newline, table_to_md(T)];
end

function s = compose_notch_doc(T)
    lines = {
        '# Dense 60 Hz Notch Reference'
        ''
        '이 문서는 60 Hz mains target에 대한 active Twin-T frequency-domain nominal reference를 정리한다.'
        '50 Hz까지 완전히 제거한다고 주장하지 않는다.'
        ''
        '## Bandwidth/Q 정의'
        ''
        '- `configured_Q`: MATLAB notch 설계에 사용한 nominal parameter이다.'
        '- `estimated_Q_from_sweep`: 30-100 Hz dense sweep에서 local passband reference magnitude 기준으로 계산한 nominal estimate이다.'
        '- `physical_Q_claim`: 실제 회로 측정 Q가 아니므로 physical Q로 주장하지 않는다.'
        ''
    };
    s = [strjoin(lines, newline), newline, table_to_md(T)];
end

function s = compose_headroom_doc(T)
    lines = {
        '# Dynamic Range and ADC Headroom Reference'
        ''
        'MATLAB nominal pre-validation을 통해 선택한 IA gain과 ADC range가 대표 ECG 입력에 대해 clipping 없이 충분한 headroom을 제공함을 확인하였다.'
        '이 결과는 representative input 기준의 nominal ADC headroom reference이다.'
        ''
    };
    s = [strjoin(lines, newline), newline, table_to_md(T)];
end

function s = compose_adc_mapping_doc(T)
    lines = {
        '# ADC Code Mapping Convention 정리'
        ''
        'MATLAB ADC output은 12-bit offset-binary code, signed decimal stream, signed 12-bit two''s-complement hex `.mem` 세 형태로 저장된다.'
        '최종 downstream digital input contract는 **1 kSPS signed 12-bit ECG stream**이며, 공식 XMODEL/RTL replay format은 **signed 12-bit two''s-complement hexadecimal `.mem`**이다.'
        ''
        '## 1. 제공하는 reference format'
        ''
        '| 파일 | 의미 | 용도 |'
        '|---|---|---|'
        '| `adc_offset_binary.mem` | physical ADC output에 해당하는 12-bit offset-binary code | ADC code convention 확인용 reference |'
        '| `adc_signed.txt` | `adc_offset_binary - 2048`로 변환한 signed decimal stream | signed stream 수치 확인용 reference |'
        '| `adc_signed_twos_complement.mem` | signed stream을 12-bit two''s-complement bit pattern으로 encoding한 3자리 대문자 hex `.mem` | 공식 downstream XMODEL/RTL replay format |'
        ''
        '`adc_signed_twos_complement.mem`의 각 line은 아래 변환과 동일하다.'
        ''
        '```matlab'
        'encoded = mod(adc_signed, 4096);'
        'fprintf(fid, ''%03X\n'', encoded);'
        '```'
        ''
        '## 2. Offset-binary와 signed stream의 관계'
        ''
        '```matlab'
        'adc_offset_binary = floor((V + 1.65)/3.3 * 4095);'
        'adc_offset_binary = min(max(adc_offset_binary, 0), 4095);'
        'adc_signed = adc_offset_binary - 2048;'
        'adc_signed_twos_complement = mod(adc_signed, 4096);'
        '```'
        ''
        '0 V는 `floor()` 사용 때문에 offset-binary 2047, signed decimal -1로 mapping된다.'
        '+1 LSB 근처의 입력은 offset-binary 2048, signed decimal 0으로 mapping된다.'
        ''
        '## 3. Downstream replay convention'
        ''
        '최종 digital input contract는 signed 12-bit ECG stream이다.'
        '따라서 RTL replay에는 `adc_signed_twos_complement.mem`을 사용한다.'
        ''
        '`adc_offset_binary.mem`은 physical ADC code reference로 보존하지만, signed input을 기대하는 RTL에 직접 넣으면 안 된다.'
        'offset-binary code를 직접 사용하는 별도 testbench에서는 반드시 mid-code subtraction 또는 convention matching을 적용해야 한다.'
        ''
        '## 4. Source ECG input code와 AFE ADC output code 구분'
        ''
        '`reference_vectors/<CLASS>/input.csv`의 `source_code_signed_est_5uV_per_code`는 원본 ECG 입력 전압 scale을 추적하기 위한 estimate이다.'
        '이 값은 AFE ADC output code가 아니다.'
        ''
        '- XMODEL analog input: `reference_vectors/<CLASS>/input.csv`의 `voltage_V`'
        '- Physical ADC code reference: `reference_vectors/<CLASS>/adc_offset_binary.mem`'
        '- Signed decimal reference: `reference_vectors/<CLASS>/adc_signed.txt`'
        '- Canonical XMODEL/RTL replay reference: `reference_vectors/<CLASS>/adc_signed_twos_complement.mem`'
        ''
        '## 5. ADC code mapping test'
        ''
        '아래 표는 `results_dataset/adc_code_mapping_test.csv`와 동일한 convention을 설명한다.'
        '해당 CSV에는 offset-binary decimal/hex, signed decimal, signed two''s-complement hex가 함께 저장된다.'
        ''
    };
    s = [strjoin(lines, newline), newline, table_to_md(T)];
end

function s = compose_input_manifest_doc(T)
    lines = {
        '# 입력 데이터셋 Manifest'
        ''
        '이 문서는 MATLAB nominal pre-validation에 사용한 source input dataset의 재현성 정보를 정리한다. 새로 clone한 환경에서 raw ECG input부터 완전 재생성하려면 `afe_input_dataset/`이 필요하다. 해당 폴더가 없으면 top-level script는 checked-in `results_dataset/` artifact를 기반으로 secondary report, figure, manifest를 재생성한다.'
        ''
        '아래 source traceability column은 대표 NSR/CHF/ARR/AFF 입력이 어느 database/record/segment에서 왔는지 추적하기 위한 정보이다. 현재 MATLAB repo에서는 exact segment start를 복구하지 않고, checked-in reference input과 SHA256 hash를 기준으로 동일성을 추적한다. 따라서 source start가 불명확한 항목은 추측하지 않고 `not tracked in this MATLAB repo; checked-in reference input and SHA256 are provided`로 명시한다.'
        ''
        '## Source traceability column 정의'
        ''
        '| Column | 의미 |'
        '|---|---|'
        '| `source_database` | upstream source database 약어 (`nsrdb`, `chfdb`, `mitdb`, `afdb`) |'
        '| `source_record_id` | source record ID |'
        '| `source_segment_start_s` | 대표 60초 segment 시작 시각. 현재 repo에서 추적되지 않으면 not tracked로 명시 |'
        '| `source_segment_duration_s` | reference input segment duration. 현재 대표 입력은 60초 기준 |'
        '| `source_selection_note` | 대표 입력 선택 목적과 주의사항 |'
        '| `source_traceability_status` | exact / partial / not tracked 중 traceability 상태. 현재는 record까지는 추적되나 exact segment start는 추적되지 않으므로 partial |'
        ''
    };
    s = [strjoin(lines, newline), newline, table_to_md(T)];
end

function s = compose_handoff_doc(p)
    lines = {
        '# MATLAB-to-XMODEL 인계 문서'
        ''
        '이 문서는 MATLAB reference output을 MATLAB-vs-XMODEL 등가성 검증에서 어떻게 사용할지 정의한다.'
        '단, 이 문서는 MATLAB과 XMODEL이 이미 bit-exact하게 일치한다는 의미가 아니다.'
        ''
        '## 1. MATLAB AFE 체인 순서'
        ''
        '```text'
        'input ECG voltage [V]'
        sprintf('→ HPF %.3f Hz', p.fc_hpf)
        sprintf('→ IA ×%.0f', p.Av_total)
        sprintf('→ 60 Hz notch, Q≈%.1f', p.Q_notch)
        sprintf('→ LPF %.1f Hz', p.fc_lpf)
        '→ ADC ±1.65 V'
        '→ 12-bit offset-binary ADC code'
        '→ signed decimal stream'
        '→ signed 12-bit two''s-complement hex .mem'
        '```'
        ''
        '## 2. 시간 영역 stream 등가성 기준'
        ''
        'XMODEL의 time-domain output은 아래 MATLAB reference와 비교한다.'
        ''
        '- `reference_vectors/<CLASS>/matlab_stage_outputs.csv`'
        '- `reference_vectors/<CLASS>/adc_offset_binary.mem`'
        '- `reference_vectors/<CLASS>/adc_signed.txt`'
        '- `reference_vectors/<CLASS>/adc_signed_twos_complement.mem`'
        ''
        '| Metric | 목표 / 설명 |'
        '|---|---|'
        '| sample alignment | lag = 0 sample |'
        '| RMS LSB error | convention을 맞춘 뒤 가능하면 2–3 LSB 이하 |'
        '| max abs LSB error | outlier 확인 |'
        '| correlation | 0.99 이상 권장 |'
        '| ADC code convention | MATLAB과 XMODEL의 offset-binary convention 일치 여부 확인 |'
        '| signed stream convention | MATLAB과 XMODEL의 signed 12-bit convention 일치 여부 확인 |'
        '| canonical replay file | `adc_signed_twos_complement.mem` 기준 |'
        ''
        '## 3. Active Twin-T notch 주파수 응답 기준'
        ''
        '60 Hz notch의 parameter-level / frequency-domain reference는 아래 결과와 비교한다.'
        ''
        '- `docs/notch_60hz_reference.md`'
        '- `results_dataset/notch_dense_sweep.csv`'
        '- `results_dataset/notch_dense_sweep_metrics.csv`'
        ''
        'MATLAB time-domain stream은 digital Q≈5 notch approximation을 사용한다.'
        '반면 dense notch sweep은 active Twin-T 구조의 frequency-domain reference를 제공한다.'
        '두 결과는 서로 관련되어 있지만, 동일한 비교 대상은 아니다.'
        '따라서 XMODEL 검증에서는 time-domain stream equivalence와 notch frequency-response validation을 분리해서 확인해야 한다.'
        ''
        '## 4. Input / Output convention'
        ''
        '- XMODEL analog input은 `reference_vectors/<CLASS>/input.csv`의 `voltage_V`를 사용한다.'
        '- `source_code_signed_est_5uV_per_code`는 source ECG scale 추적용 estimate이며, AFE ADC output code가 아니다.'
        '- `adc_offset_binary.mem`은 physical ADC offset-binary code convention 확인용 reference이다.'
        '- `adc_signed.txt`는 offset-binary code에서 mid-code 2048을 제거한 signed decimal stream reference이다.'
        '- `adc_signed_twos_complement.mem`은 공식 downstream XMODEL/RTL replay format이다.'
        '- 최종 digital input contract는 1 kSPS signed 12-bit ECG stream이다.'
        ''
        '## 5. Canonical downstream replay format'
        ''
        '수환 XMODEL 저장소와 양건 locked digital RTL testbench의 최종 interface는 아래 형식으로 확정되었다.'
        ''
        '```text'
        '1 kSPS signed 12-bit two''s-complement hexadecimal .mem'
        'one sample per line'
        '3 uppercase hex digits per line'
        '```'
        ''
        '`adc_signed_twos_complement.mem`은 아래 MATLAB 변환과 동일하다.'
        ''
        '```matlab'
        'encoded = mod(adc_signed, 4096);'
        'fprintf(fid, ''%03X\n'', encoded);'
        '```'
        ''
        '따라서 offset-binary code를 RTL에 직접 넣지 않는다.'
        'offset-binary code를 사용하는 별도 테스트 경로가 있다면 명시적인 mid-code subtraction 또는 convention matching을 적용해야 한다.'
        ''
        '## 6. Reference vector 검증'
        ''
        '`reference_vectors/reference_vector_manifest.csv`는 모든 reference vector 파일의 byte 수와 SHA256을 기록한다.'
        'line ending 차이로 hash가 바뀌지 않도록 `.gitattributes`에서 reference vector 파일의 line ending을 LF로 고정한다.'
        '검증은 아래 MATLAB script로 수행한다.'
        ''
        '```matlab'
        'verify_reference_vector_manifest'
        '```'
        ''
        '하나라도 파일 누락, byte 수 불일치, SHA256 불일치가 발생하면 warning이 아니라 MATLAB error로 실패한다.'
    };
    s = strjoin(lines, newline);
end

function s = compose_validation_status_doc()
    lines = {
        '# 검증 상태 정리'
        ''
        '이 문서는 MATLAB repo가 주장할 수 있는 범위와 후속 XMODEL/digital 파트로 넘겨야 하는 범위를 정리한다.'
        ''
        '| Item | Status | Artifact | Note |'
        '|---|---|---|---|'
        '| Parameter reference | PASS | `docs/afe_adc_parameter_reference.md` | XMODEL nominal 기준 |'
        '| Frequency response reference | PASS | `docs/frequency_response_reference.md` | 60 Hz ideal digital zero caveat 및 passband-relative column 포함 |'
        '| Dense 60 Hz notch reference | PASS/PARTIAL | `docs/notch_60hz_reference.md` | bandwidth/Q는 nominal estimate, physical Q 아님 |'
        '| Dynamic range / headroom | PASS | `docs/dynamic_range_headroom_reference.md` | representative inputs 기준 clipping 0% |'
        '| ADC code mapping | PASS | `docs/adc_code_mapping_convention.md` | offset-binary, signed decimal, signed two''s-complement hex convention 명시 |'
        '| Downstream canonical replay format | PASS | `reference_vectors/<CLASS>/adc_signed_twos_complement.mem` | 1 kSPS signed 12-bit two''s-complement hex `.mem`, 한 줄당 3자리 대문자 hex |'
        '| Reference vectors | PASS | `reference_vectors/reference_vector_manifest.md` | NSR/CHF/ARR/AFF SHA256 tracked, signed two''s-complement `.mem` 포함 |'
        '| Reference vector manifest verification | PASS | `verify_reference_vector_manifest.m` | 파일 존재 여부, byte 수, SHA256 불일치 시 MATLAB error |'
        '| Input dataset source traceability | PARTIAL | `docs/INPUT_DATASET_MANIFEST.md` | source database/record는 기록, exact segment start는 이 MATLAB repo에서 not tracked |'
        '| MATLAB-vs-XMODEL equivalence | NOT DONE | XMODEL 담당 | claim 금지 |'
        '| CMRR / op-amp / ADC nonideal | NOT DONE | XMODEL 또는 analog stress 검증 | claim 금지 |'
        '| PCB / silicon / clinical validation | NOT DONE | scope 밖 | claim 금지 |'
        '| Board replay / final classification accuracy | NOT DONE | digital/integration 담당 | MATLAB repo 범위 밖 |'
        ''
        '## 최종 claim'
        ''
        'MATLAB 단계는 SystemVerilog XMODEL 구현 이전의 nominal system-level pre-validation 및 reference generation 단계이다.'
        '본 단계는 schematic 기반 AFE 필터 파라미터, frequency-response reference, ADC headroom, code-mapping convention, 그리고 대표 NSR/CHF/ARR/AFF 입력에 대한 SHA256-tracked reference vector를 정의한다.'
        '본 단계는 transistor-level, PCB-level, silicon-level, clinical validation 또는 MATLAB-vs-XMODEL bit-exact equivalence를 주장하지 않는다.'
    };
    s = strjoin(lines, newline);
end

function s = compose_figure_captions_doc()
    note_ko = '본 figure는 SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과이며, transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL 등가성 검증을 의미하지 않는다.';
    lines = {
        '# Figure Captions'
        ''
        '본 문서는 `figures/` 폴더에 저장된 주요 figure를 논문 또는 보고서에 사용할 때 적용할 caption 문구를 정리한다.'
        ''
        '모든 figure는 **SystemVerilog XMODEL 구현 전 MATLAB nominal reference 결과**를 나타낸다. 따라서 아래 figure들은 transistor-level, PCB-level, silicon-level 검증 또는 MATLAB-vs-XMODEL bit-exact 등가성 검증을 의미하지 않는다.'
        ''
        '## 공통 주의 문구'
        ''
        '```text'
        note_ko
        '```'
        ''
        '## Figure별 권장 Caption'
        ''
        '| Figure | 권장 caption / note |'
        '|---|---|'
        ['| `fig_matlab_prevalidation_flow` | SystemVerilog XMODEL 구현 전 MATLAB nominal pre-validation과 reference generation의 전체 흐름을 나타낸다. ' note_ko ' |']
        ['| `fig_afe_chain_overview` | MATLAB nominal model에서 사용한 AFE+ADC 신호 처리 체인을 나타낸다. 입력 ECG 전압은 HPF, IA, 60 Hz notch, LPF, ADC quantizer를 거쳐 offset-binary ADC code, signed decimal stream, signed two''s-complement hex `.mem`으로 변환된다. ' note_ko ' |']
        ['| `fig_total_frequency_response` | MATLAB nominal AFE+ADC chain의 전체 frequency response reference를 나타낸다. HPF cutoff, 60 Hz notch target, LPF cutoff를 확인하기 위한 기준 그래프이다. 단, MATLAB time-domain digital notch approximation의 60 Hz ideal zero는 실제 analog attenuation claim이 아니다. ' note_ko ' |']
        ['| `fig_notch_dense_sweep` | Active Twin-T 60 Hz notch의 dense frequency-domain reference를 나타낸다. 본 figure는 60 Hz target notch 특성을 보여주며, 50 Hz까지 완전 제거한다고 주장하지 않는다. ' note_ko ' |']
        ['| `fig_dynamic_range_headroom` | 대표 NSR/CHF/ARR/AFF 입력에 대한 ADC rail 대비 AFE 출력 headroom을 나타낸다. 모든 클래스에서 clipping ratio가 0%임을 nominal 기준에서 확인하기 위한 figure이다. ' note_ko ' |']
        ['| `fig_adc_code_distribution` | 대표 ECG 입력에서 생성된 ADC code distribution을 나타낸다. ADC code가 0 또는 4095 rail에 붙지 않는지 확인하기 위한 figure이며, downstream RTL replay의 canonical format은 signed two''s-complement `.mem`이다. ' note_ko ' |']
        ['| `fig_reference_vector_handoff` | MATLAB reference vector가 후속 XMODEL 등가성 검증 및 locked digital RTL replay로 전달되는 흐름을 나타낸다. canonical replay vector는 `adc_signed_twos_complement.mem`이다. ' note_ko ' |']
    };
    s = strjoin(lines, newline);
end

function s = table_to_md(T)
    % MATLAB version-compatible Markdown table writer.
    % Avoids cell arrays of string objects such as {"---"}, which fail in
    % some MATLAB releases where strjoin expects char-vector cell arrays.
    vars = T.Properties.VariableNames;
    vars = cellfun(@char, vars, 'UniformOutput', false);

    s = ['| ' strjoin(vars, ' | ') ' |' newline];
    s = [s '|' strjoin(repmat({'---'}, 1, numel(vars)), '|') '|' newline];

    for i = 1:height(T)
        vals = cell(1, numel(vars));
        for j = 1:numel(vars)
            x = T{i,j};
            if isnumeric(x)
                if isempty(x)
                    vals{j} = '';
                elseif isscalar(x) && isnan(x)
                    vals{j} = '';
                elseif isscalar(x)
                    vals{j} = num2str(x, '%.12g');
                else
                    vals{j} = mat2str(x);
                end
            elseif isstring(x)
                vals{j} = char(x);
            elseif iscell(x)
                if isempty(x)
                    vals{j} = '';
                else
                    vals{j} = char(string(x{1}));
                end
            elseif ischar(x)
                vals{j} = x;
            else
                vals{j} = char(string(x));
            end

            vals{j} = strrep(vals{j}, '|', '\|');
            vals{j} = strrep(vals{j}, newline, '<br>');
        end
        s = [s '| ' strjoin(vals, ' | ') ' |' newline]; %#ok<AGROW>
    end
end
