function run_fixed_matlab_patient()
% Execute the exact fixed-commit MATLAB model on the workspace patient PWL.
root = fileparts(fileparts(mfilename('fullpath')));
fixed_dir = fullfile(root, 'reference', 'matlab_fixed_907f7e1', 'matlab_afe_validation');
exec_dir = fullfile(root, 'results', 'nominal', 'matlab_fixed_execution');
input_dir = fullfile(exec_dir, 'input_data');
if ~exist(input_dir, 'dir'); mkdir(input_dir); end
% The fixed generate_ecg_input.m has a two-column .txt loader defect: it
% interprets column 1 (time) as voltage. Use the exact same bytes with .pwl
% extension so the fixed parse_pwl_file.m path handles time/voltage correctly.
copyfile(fullfile(fileparts(root), 'patient100_ecg_10s.txt'), fullfile(input_dir, 'patient100_ecg_10s.pwl'));
addpath(fixed_dir);
old_dir = pwd;
cleanup = onCleanup(@() cd(old_dir));
cd(exec_dir);
p = afe_adc_params();
filt = design_afe_filters(p);
[t, v_ecg_diff, input_source] = generate_ecg_input(p, 10);
[y, metrics] = afe_adc_model(t, v_ecg_diff, p, filt);
T = table(y.time_s, y.v_diff, y.v_hpf, y.v_ia, y.v_notch, y.v_lpf, ...
          y.v_adc_in, y.adc_code, y.adc_signed, ...
          'VariableNames', {'time_s','v_diff','v_hpf','v_ia','v_notch','v_lpf', ...
                            'v_adc_in','adc_code','adc_signed'});
writetable(T, fullfile(exec_dir, 'matlab_fixed_patient100_output.csv'));
writetable(metrics, fullfile(exec_dir, 'matlab_fixed_patient100_metrics.csv'));
fid = fopen(fullfile(exec_dir, 'execution.txt'), 'w');
fprintf(fid, 'fixed_commit=907f7e1f081a9d6a5703a32095d962143315a192\n');
fprintf(fid, 'matlab_version=%s\n', version);
fprintf(fid, 'input_source=%s\n', input_source);
fprintf(fid, 'sample_count=%d\n', numel(t));
fprintf(fid, 'time_start_s=%.12g\n', t(1));
fprintf(fid, 'time_end_s=%.12g\n', t(end));
fclose(fid);
disp(metrics);
end
