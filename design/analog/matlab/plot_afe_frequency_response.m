function plot_afe_frequency_response(p, filt, results_dir)
%PLOT_AFE_FREQUENCY_RESPONSE  Plot overall AFE response and active Twin-T notch.

    if nargin < 3
        results_dir = 'results';
    end
    if ~exist(results_dir, 'dir')
        mkdir(results_dir);
    end

    [f, H_hpf]   = freq_response_discrete(filt.b_hpf,   filt.a_hpf,   p.fs, 8192);
    [~, H_notch] = freq_response_discrete(filt.b_notch, filt.a_notch, p.fs, 8192);
    [~, H_lpf]   = freq_response_discrete(filt.b_lpf,   filt.a_lpf,   p.fs, 8192);

    H_total = p.Av_total .* H_hpf .* H_notch .* H_lpf;

    figure;
    semilogx(f, 20*log10(abs(H_total) + eps), 'LineWidth', 1.5);
    grid on;
    xlabel('Frequency [Hz]');
    ylabel('Magnitude [dB]');
    title('Total AFE Frequency Response');
    xlim([0.1 500]);
    yline(20*log10(p.Av_total), '--', 'Passband gain target');
    xline(p.fc_hpf, '--', sprintf('HPF %.3f Hz', p.fc_hpf));
    xline(p.f_notch, '--', '60 Hz notch');
    xline(p.fc_lpf, '--', sprintf('LPF %.1f Hz', p.fc_lpf));
    saveas(gcf, fullfile(results_dir, 'fig_total_frequency_response.png'));

    % Exact analog active Twin-T response using nodal analysis.
    f_sweep = logspace(log10(0.1), log10(500), 3000).';
    H_twin = active_twin_t_response(f_sweep, p.R_twin, p.C_twin, p.k_boot);

    figure;
    semilogx(f_sweep, 20*log10(abs(H_twin) + eps), 'LineWidth', 1.5);
    grid on;
    xlabel('Frequency [Hz]');
    ylabel('Magnitude [dB]');
    title('Active Twin-T Notch Response');
    xlim([0.1 500]);
    xline(60, '--', '60 Hz');
    saveas(gcf, fullfile(results_dir, 'fig_active_twin_t_notch_response.png'));
end
