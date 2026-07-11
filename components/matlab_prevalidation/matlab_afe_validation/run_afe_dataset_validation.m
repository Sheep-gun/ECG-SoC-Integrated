%% ================================================================
%  Official AFE Input Dataset Batch Validation
%
%  Required 4-class dataset:
%    afe_input_dataset/afe_input_NSR.csv
%    afe_input_dataset/afe_input_CHF.csv
%    afe_input_dataset/afe_input_ARR.csv
%    afe_input_dataset/afe_input_AFF.csv
%
%  Optional:
%    afe_input_dataset/afe_input_record100_NSR.csv
%
%  Each official CSV: sample_index, time_s, code_signed, voltage_V
%  Each PWL: time[s], voltage[V]
%
%  Run:
%    run_afe_dataset_validation
% ================================================================

clear; clc; close all;
rng(7);

results_dir = 'results_dataset';
if ~exist(results_dir, 'dir')
    mkdir(results_dir);
end

p = afe_adc_params();
filt = design_afe_filters(p);

% Save schematic-level parameter summary and common frequency response.
print_afe_spec_summary(p, results_dir);
plot_afe_frequency_response(p, filt, results_dir);

required_records = {'NSR', 'CHF', 'ARR', 'AFF'};
optional_records = {'record100_NSR'};
prefer_format = 'csv';   % CSV is recommended for MATLAB analysis. Use 'pwl' to test PWL parsing.

all_metrics = table();
all_meta = table();

% Required records: fail-fast.
for i = 1:numel(required_records)
    rec = required_records{i};
    fprintf('\n===== Validating required record %s =====\n', rec);

    [t, v_ecg_diff, src, meta] = load_afe_input_record(rec, p, prefer_format);
    fprintf('Input source: %s\n', src);

    assert_required_input_record(t, v_ecg_diff, rec, p);

    [y, metrics] = afe_adc_model(t, v_ecg_diff, p, filt);
    assert_required_output_record(y, rec, p);

    metrics.record_name = string(rec);
    metrics = movevars(metrics, 'record_name', 'Before', 1);
    meta.record_name = string(rec);

    rec_dir = fullfile(results_dir, rec);
    if ~exist(rec_dir, 'dir')
        mkdir(rec_dir);
    end

    plot_afe_time_domain(y, p, rec_dir);
    save_afe_outputs(y, metrics, rec_dir);

    assert_required_saved_outputs(rec_dir, rec);

    all_metrics = [all_metrics; metrics]; %#ok<AGROW>
    all_meta = [all_meta; meta]; %#ok<AGROW>

    disp(metrics);
end

% Optional records: warn and continue.
for i = 1:numel(optional_records)
    rec = optional_records{i};
    fprintf('\n===== Validating optional record %s =====\n', rec);
    try
        [t, v_ecg_diff, src, meta] = load_afe_input_record(rec, p, prefer_format);
        fprintf('Input source: %s\n', src);

        [y, metrics] = afe_adc_model(t, v_ecg_diff, p, filt);

        metrics.record_name = string(rec);
        metrics = movevars(metrics, 'record_name', 'Before', 1);
        meta.record_name = string(rec);

        rec_dir = fullfile(results_dir, rec);
        if ~exist(rec_dir, 'dir')
            mkdir(rec_dir);
        end

        plot_afe_time_domain(y, p, rec_dir);
        save_afe_outputs(y, metrics, rec_dir);

        all_metrics = [all_metrics; metrics]; %#ok<AGROW>
        all_meta = [all_meta; meta]; %#ok<AGROW>

        disp(metrics);
    catch ME
        warning('Optional record %s skipped: %s', rec, ME.message);
    end
end

writetable(all_metrics, fullfile(results_dir, 'afe_dataset_dynamic_range_summary.csv'));
writetable(all_meta, fullfile(results_dir, 'afe_dataset_input_summary.csv'));

fprintf('\nBatch validation finished. Results saved in ./%s/\n', results_dir);

function assert_required_input_record(t, v, rec, p)
    if numel(t) ~= 60000 || numel(v) ~= 60000
        error('run_afe_dataset_validation:BadInputLength', ...
              '%s must contain 60000 samples after loading, got t=%d v=%d', rec, numel(t), numel(v));
    end
    dt = median(diff(t));
    fs_est = 1/dt;
    if abs(fs_est - p.fs) > 1e-6
        error('run_afe_dataset_validation:BadInputFs', ...
              '%s must be 1 kSPS, got %.9g Hz', rec, fs_est);
    end
    if any(~isfinite(v))
        error('run_afe_dataset_validation:BadInputValue', ...
              '%s contains non-finite input voltage values', rec);
    end
end

function assert_required_output_record(y, rec, p)
    n = numel(y.time_s);
    if n ~= 60000
        error('run_afe_dataset_validation:BadOutputLength', ...
              '%s must generate 60000 output samples, got %d', rec, n);
    end
    required = {'v_diff','v_hpf','v_ia','v_notch','v_lpf','v_adc_in','adc_code','adc_signed'};
    for k = 1:numel(required)
        if ~isfield(y, required{k})
            error('run_afe_dataset_validation:MissingOutputField', ...
                  '%s output missing field %s', rec, required{k});
        end
        if numel(y.(required{k})) ~= n
            error('run_afe_dataset_validation:BadOutputFieldLength', ...
                  '%s output field %s length mismatch', rec, required{k});
        end
    end
    if any(y.adc_code < 0 | y.adc_code > p.adc_max)
        error('run_afe_dataset_validation:AdcCodeOutOfRange', ...
              '%s ADC offset-binary code out of range', rec);
    end
end

function assert_required_saved_outputs(rec_dir, rec)
    required_files = { ...
        'matlab_afe_adc_output.csv', ...
        'matlab_adc_offset_binary_hex.mem', ...
        'matlab_adc_signed_decimal.txt'};
    for k = 1:numel(required_files)
        f = fullfile(rec_dir, required_files{k});
        if ~exist(f, 'file')
            error('run_afe_dataset_validation:MissingSavedOutput', ...
                  '%s missing saved output %s', rec, f);
        end
    end
end
