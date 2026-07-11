function [t, v_ecg_diff, src, meta] = load_afe_input_record(record_name, p, prefer_format)
%LOAD_AFE_INPUT_RECORD  Load official AFE input dataset record.
%
% Supported official repo dataset layout:
%   afe_input_dataset/afe_input_{NSR,CHF,ARR,AFF}.csv
%   afe_input_dataset/afe_input_{NSR,CHF,ARR,AFF}.pwl
%   afe_input_dataset/afe_input_record100_NSR.csv
%   afe_input_dataset/afe_input_record100_NSR.pwl
%
% CSV expected columns:
%   sample_index, time_s, code_signed, voltage_V
%
% PWL expected columns:
%   time[s], voltage[V]
%
% Output convention:
%   t           : time vector at p.fs [s]
%   v_ecg_diff  : AFE differential input voltage [V]
%   src         : human-readable input source description
%   meta        : table with input statistics

    if nargin < 3 || isempty(prefer_format)
        prefer_format = 'csv';
    end

    record_name = char(record_name);
    prefer_format = lower(char(prefer_format));

    if startsWith(record_name, 'afe_input_')
        base_name = record_name;
    else
        base_name = ['afe_input_' record_name];
    end

    search_dirs = { ...
        'afe_input_dataset', ...
        fullfile('..', 'afe_input_dataset'), ...
        fullfile('input_data', 'afe_input_dataset'), ...
        'input_data', ...
        '.'};

    if strcmp(prefer_format, 'pwl')
        exts = {'.pwl', '.csv'};
    else
        exts = {'.csv', '.pwl'};
    end

    input_file = '';
    for d = 1:numel(search_dirs)
        for e = 1:numel(exts)
            candidate = fullfile(search_dirs{d}, [base_name exts{e}]);
            if exist(candidate, 'file')
                input_file = candidate;
                break;
            end
        end
        if ~isempty(input_file)
            break;
        end
    end

    if isempty(input_file)
        error('load_afe_input_record:FileNotFound', ...
            ['Could not find %s.csv or %s.pwl. Copy the repo folder ', ...
             'afe_input_dataset/ into this MATLAB validation folder, ', ...
             'or place files under input_data/.'], base_name, base_name);
    end

    [~, ~, ext] = fileparts(input_file);
    ext = lower(ext);

    if strcmp(ext, '.csv')
        T = readtable(input_file);
        names = T.Properties.VariableNames;

        if any(strcmp(names, 'voltage_V'))
            v_file = T.voltage_V;
        elseif width(T) >= 4
            v_file = T{:,4};
        elseif width(T) >= 2
            v_file = T{:,2};
        else
            error('load_afe_input_record:BadCSV', ...
                  'CSV must contain voltage_V or at least two numeric columns.');
        end

        if any(strcmp(names, 'time_s'))
            t_file = T.time_s;
        elseif any(strcmp(names, 'sample_index'))
            t_file = double(T.sample_index) / p.fs;
        else
            t_file = (0:numel(v_file)-1).' / p.fs;
        end

        fmt = 'csv';
    elseif strcmp(ext, '.pwl')
        data = parse_pwl_file(input_file);
        t_file = data(:,1);
        v_file = data(:,2);
        fmt = 'pwl';
    else
        error('load_afe_input_record:UnsupportedExtension', ...
              'Unsupported file extension: %s', ext);
    end

    t_file = t_file(:);
    v_file = v_file(:);

    ok = isfinite(t_file) & isfinite(v_file);
    t_file = t_file(ok);
    v_file = v_file(ok);

    [t_file, idx] = unique(t_file, 'stable');
    v_file = v_file(idx);

    if numel(t_file) < 2
        error('load_afe_input_record:TooShort', 'Input record has fewer than two samples.');
    end

    file_dt = median(diff(t_file));
    file_fs = 1/file_dt;

    % Resample/interpolate to AFE XModel ADC rate.
    t_file0 = t_file - t_file(1);
    duration_s = t_file0(end) + file_dt;
    t = (0:1/p.fs:duration_s-1/p.fs).';
    v_ecg_diff = interp1(t_file0, v_file, t, 'linear', 'extrap');

    src = sprintf('%s (%s), original_fs=%.3fHz, resampled_to=%.1fHz', ...
                  input_file, fmt, file_fs, p.fs);

    meta = table( ...
        string(record_name), string(input_file), string(fmt), ...
        file_fs, p.fs, numel(v_file), numel(v_ecg_diff), ...
        duration_s, min(v_file), max(v_file), peak2peak(v_file), rms(v_file), ...
        'VariableNames', { ...
        'record_name','input_file','format','original_fs_Hz','target_fs_Hz', ...
        'original_samples','resampled_samples','duration_s', ...
        'input_min_V','input_max_V','input_pp_V','input_rms_V'});
end
