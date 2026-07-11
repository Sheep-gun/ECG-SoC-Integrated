function [t, v_ecg_diff, src] = generate_ecg_input(p, Tsim)
%GENERATE_ECG_INPUT  Load ECG input data and resample to AFE ADC rate.
%
% Input convention:
%   v_ecg_diff = v_ecg_pos - v_ecg_neg  [V]
%
% Preferred real ECG input:
%   input_data/patient100_ecg_10s.pwl
%   input_data/patient100_ecg_10s.txt
%     two columns: [time_s, ecg_voltage_V]
%
% Other optional inputs:
%   ecg_input.pwl
%   ecg_input.csv
%   ecg_input.txt
%     format A: [time_s, ecg_voltage_V]
%     format B: [ecg_voltage_V]
%
% PWL support:
%   - Plain numeric two-column PWL files are supported.
%   - LTspice-style PWL files with suffixes such as m, u, n are supported
%     through parse_pwl_file.m.
%
% If the input file sampling rate differs from p.fs, the waveform is
% linearly interpolated to the AFE+ADC sampling rate. In this project,
% the patient #100 10-second ECG file is sampled at about 360 Hz, while
% the AFE+ADC XModel uses 1 kSPS. Therefore, resampling to 1 kSPS is
% required before AFE+ADC validation.

    if nargin < 2
        Tsim = 10;
    end

    fs = p.fs;
    t_default = (0:1/fs:Tsim-1/fs).';

    candidate_files = { ...
        fullfile('afe_input_dataset', 'afe_input_NSR.csv'), ...
        fullfile('afe_input_dataset', 'afe_input_NSR.pwl'), ...
        fullfile('input_data', 'patient100_ecg_10s.pwl'), ...
        fullfile('input_data', 'patient100_ecg_10s.txt'), ...
        'ecg_input.pwl', ...
        'ecg_input.csv', ...
        'ecg_input.txt'};

    input_file = '';
    for k = 1:numel(candidate_files)
        if exist(candidate_files{k}, 'file')
            input_file = candidate_files{k};
            break;
        end
    end

    if ~isempty(input_file)
        [~, ~, ext] = fileparts(input_file);
        ext = lower(ext);

        if strcmp(ext, '.pwl')
            data = parse_pwl_file(input_file);
            t_file = data(:,1);
            v_file = data(:,2);
            data = [];
        elseif strcmp(ext, '.csv')
            [t_file, v_file, data] = read_ecg_csv_with_header_support(input_file);
        else
            data = readmatrix(input_file);
            data = data(all(~isnan(data), 2), :);
            t_file = [];
            v_file = [];
        end

        if ~isempty(t_file) && ~isempty(v_file)
            % Header-based CSV or PWL path already selected time_s/voltage_V explicitly.

            % Ensure monotonically increasing time values.
            [t_file, idx] = unique(t_file, 'stable');
            v_file = v_file(idx);

            if numel(t_file) < 2
                error('generate_ecg_input:TooShort', ...
                      'Input file must contain at least two time samples.');
            end

            file_dt = median(diff(t_file));
            file_fs = 1/file_dt;

            % Use the shorter of requested Tsim and the file duration.
            t_end = min(Tsim, t_file(end) - t_file(1) + file_dt);
            t = (0:1/fs:t_end-1/fs).';

            % Align file time to start at 0 s, then interpolate to AFE fs.
            t_file0 = t_file - t_file(1);
            v_ecg_diff = interp1(t_file0, v_file, t, 'linear', 'extrap');

            src = sprintf('%s, original_fs=%.3fHz, resampled_to=%.1fHz', ...
                          input_file, file_fs, fs);
        else
            v_file = data(:,1);
            n = min(length(t_default), length(v_file));
            t = t_default(1:n);
            v_ecg_diff = v_file(1:n);
            src = sprintf('%s, single-column voltage input', input_file);
        end
    else
        t = t_default;
        v_ecg_diff = synthetic_ecg_like(t);
        src = 'synthetic_ecg_like';
    end

    % Add controlled non-ideal input components for stress validation.
    % For the official afe_input_dataset files, keep this false so MATLAB
    % validates the exact repo waveform. Change to true only when you want
    % to inject baseline wander / 60Hz PLI / noise deliberately.
    add_artifacts = false;

    if add_artifacts
        baseline = 0.25e-3 * sin(2*pi*0.25*t);   % 0.25 mV baseline wander
        pli60    = 0.20e-3 * sin(2*pi*60*t);     % 0.20 mV differential 60Hz PLI
        noise    = 0.03e-3 * randn(size(t));     % small wideband noise
        v_ecg_diff = v_ecg_diff + baseline + pli60 + noise;
    end
end


function [t_file, v_file, data] = read_ecg_csv_with_header_support(input_file)
%READ_ECG_CSV_WITH_HEADER_SUPPORT
% Official AFE input CSV format:
%   sample_index,time_s,code_signed,voltage_V
% Legacy CSV format:
%   [time_s, voltage_V] or [voltage_V]

    t_file = [];
    v_file = [];
    data = [];

    try
        T = readtable(input_file);
        names = T.Properties.VariableNames;
        if any(strcmp(names, 'time_s')) && any(strcmp(names, 'voltage_V'))
            t_file = T.time_s;
            v_file = T.voltage_V;
            return;
        elseif any(strcmp(names, 'voltage_V'))
            v_file = T.voltage_V;
            t_file = (0:numel(v_file)-1).';
            return;
        end
    catch
        % Fall back to numeric legacy parsing below.
    end

    data = readmatrix(input_file);
    data = data(all(~isnan(data), 2), :);
    if size(data,2) >= 2
        t_file = data(:,1);
        v_file = data(:,2);
    end
end


function ecg = synthetic_ecg_like(t)
%SYNTHETIC_ECG_LIKE  Simple ECG-like waveform, peak around 1 mV.
% This is only for validation when no real ECG input file is supplied.

    ecg = zeros(size(t));
    rr = 0.85;                       % roughly 70 bpm
    r_times = 0.8:rr:max(t);

    for r = r_times
        ecg = ecg + 0.12e-3 * exp(-((t-(r-0.18))/0.045).^2);  % P
        ecg = ecg - 0.20e-3 * exp(-((t-(r-0.035))/0.015).^2); % Q
        ecg = ecg + 1.00e-3 * exp(-((t-r)/0.018).^2);         % R
        ecg = ecg - 0.25e-3 * exp(-((t-(r+0.035))/0.018).^2); % S
        ecg = ecg + 0.30e-3 * exp(-((t-(r+0.25))/0.080).^2);  % T
    end
end
