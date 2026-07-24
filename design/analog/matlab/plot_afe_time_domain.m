function plot_afe_time_domain(y, p, results_dir)
%PLOT_AFE_TIME_DOMAIN  Plot input, intermediate AFE output, and ADC code.

    if nargin < 3
        results_dir = 'results';
    end
    if ~exist(results_dir, 'dir')
        mkdir(results_dir);
    end

    t = y.time_s;
    xmax = min(5, max(t));

    figure;
    plot(t, y.v_diff*1e3, 'LineWidth', 1.0);
    grid on;
    xlabel('Time [s]');
    ylabel('Differential ECG [mV]');
    title('Input Differential ECG');
    xlim([0 xmax]);
    saveas(gcf, fullfile(results_dir, 'fig_input_differential_ecg.png'));

    figure;
    plot(t, y.v_hpf*1e3, 'LineWidth', 1.0);
    grid on;
    xlabel('Time [s]');
    ylabel('HPF Output [mV]');
    title('After HPF: Baseline Removal');
    xlim([0 xmax]);
    saveas(gcf, fullfile(results_dir, 'fig_after_hpf.png'));

    figure;
    plot(t, y.v_ia, 'LineWidth', 1.0);
    grid on;
    xlabel('Time [s]');
    ylabel('IA Output [V]');
    title('After IA Gain');
    xlim([0 xmax]);
    saveas(gcf, fullfile(results_dir, 'fig_after_ia_gain.png'));

    figure;
    plot(t, y.v_lpf, 'LineWidth', 1.0);
    hold on;
    yline(p.vref_p, '--', '+1.65 V');
    yline(p.vref_n, '--', '-1.65 V');
    grid on;
    xlabel('Time [s]');
    ylabel('ADC Input [V]');
    title('AFE Output Before ADC');
    xlim([0 xmax]);
    saveas(gcf, fullfile(results_dir, 'fig_afe_output_before_adc.png'));

    figure;
    plot(t, y.adc_code, 'LineWidth', 1.0);
    grid on;
    xlabel('Time [s]');
    ylabel('ADC Code [0 to 4095]');
    title('12-bit Offset-Binary ADC Output');
    xlim([0 xmax]);
    saveas(gcf, fullfile(results_dir, 'fig_adc_code_time_domain.png'));

    figure;
    histogram(y.adc_code, 80);
    grid on;
    xlabel('ADC Code');
    ylabel('Count');
    title('ADC Code Distribution');
    saveas(gcf, fullfile(results_dir, 'fig_adc_code_distribution.png'));
end
