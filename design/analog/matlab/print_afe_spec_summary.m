function spec_table = print_afe_spec_summary(p, results_dir)
%PRINT_AFE_SPEC_SUMMARY  Print and save schematic-derived design summary.

    spec_table = table( ...
        p.fc_hpf, p.Av_ia, p.Av_total, p.f_notch, p.k_boot, p.Q_notch, ...
        p.fc_lpf, p.vref_n, p.vref_p, p.adc_bits, p.A_OL_dB, p.CMRR_dB, ...
        'VariableNames', { ...
        'HPF_fc_Hz', 'IA_Gain', 'Total_Gain', 'Notch_f0_Hz', ...
        'Bootstrap_k', 'Notch_Q', 'LPF_fc_Hz', 'ADC_Vref_N', ...
        'ADC_Vref_P', 'ADC_bits', 'Opamp_AOL_dB', 'Opamp_CMRR_dB'});

    disp('===== AFE+ADC schematic parameter summary =====');
    disp(spec_table);

    if nargin >= 2 && ~isempty(results_dir)
        if ~exist(results_dir, 'dir')
            mkdir(results_dir);
        end
        writetable(spec_table, fullfile(results_dir, 'afe_adc_spec_summary.csv'));
    end
end
