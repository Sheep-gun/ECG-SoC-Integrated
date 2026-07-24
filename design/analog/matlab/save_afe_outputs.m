function save_afe_outputs(y, metrics, results_dir)
%SAVE_AFE_OUTPUTS  Save MATLAB validation outputs as CSV/TXT/MEM files.

    if nargin < 3
        results_dir = 'results';
    end
    if ~exist(results_dir, 'dir')
        mkdir(results_dir);
    end

    writetable(metrics, fullfile(results_dir, 'afe_adc_dynamic_range_metrics.csv'));

    out_table = table( ...
        y.time_s, y.v_diff, y.v_hpf, y.v_ia, y.v_notch, y.v_lpf, y.v_adc_in, ...
        y.adc_code, y.adc_signed, ...
        'VariableNames', {'time_s','v_diff','v_hpf','v_ia','v_notch', ...
                          'v_lpf','v_adc_in','adc_code','adc_signed'});

    writetable(out_table, fullfile(results_dir, 'matlab_afe_adc_output.csv'));
    writematrix(y.adc_signed, fullfile(results_dir, 'matlab_adc_signed_decimal.txt'));

    % Offset-binary 12-bit hex memory file, usable for simple RTL replay.
    fid = fopen(fullfile(results_dir, 'matlab_adc_offset_binary_hex.mem'), 'w');
    for i = 1:length(y.adc_code)
        fprintf(fid, '%03X\n', y.adc_code(i));
    end
    fclose(fid);
end
