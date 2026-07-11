%% ================================================================
%  AFE+ADC MATLAB Validation Main Script
%
%  Intended report flow:
%    Existing analog schematic
%      -> MATLAB validation of gain / filters / ADC dynamic range
%      -> SystemVerilog XModel implementation
%
%  How to run:
%    1) Put all .m files in one folder.
%    2) Optional: put ecg_input.csv in the same folder.
%    3) Run this file in MATLAB.
% ================================================================

clear; clc; close all;
rng(7);  % reproducible input noise

results_dir = 'results';
if ~exist(results_dir, 'dir')
    mkdir(results_dir);
end

%% 1. Load schematic-derived parameters
p = afe_adc_params();
spec_table = print_afe_spec_summary(p, results_dir); %#ok<NASGU>

%% 2. Design MATLAB validation filters
filt = design_afe_filters(p);

%% 3. Frequency-domain validation
plot_afe_frequency_response(p, filt, results_dir);

%% 4. Time-domain ECG validation
Tsim = 10;  % seconds
[t, v_ecg_diff, input_source] = generate_ecg_input(p, Tsim);
fprintf('Input source: %s\n', input_source);

[y, metrics] = afe_adc_model(t, v_ecg_diff, p, filt);

disp('===== Time-domain / ADC dynamic range metrics =====');
disp(metrics);

%% 5. Plot and save outputs
plot_afe_time_domain(y, p, results_dir);
save_afe_outputs(y, metrics, results_dir);

fprintf('\nValidation finished. Results saved in ./%s/\n', results_dir);
