function filt = design_afe_filters(p)
%DESIGN_AFE_FILTERS  Create digital validation filters from schematic specs.
%
% These filters are not intended to replace the analog schematic.
% They are MATLAB validation equivalents used to check whether the schematic
% values lead to the intended system-level AFE response.

    fs = p.fs;

    [filt.b_hpf, filt.a_hpf] = first_order_hpf(p.fc_hpf, fs);
    [filt.b_lpf, filt.a_lpf] = first_order_lpf(p.fc_lpf, fs);
    [filt.b_notch, filt.a_notch] = second_order_notch(p.f_notch, p.Q_notch, fs);
end

function [b, a] = first_order_lpf(fc, fs)
%FIRST_ORDER_LPF  Bilinear-transform equivalent of H(s)=wc/(s+wc).
    wc = 2*pi*fc;
    K  = 2*fs;

    b = [wc, wc] / (K + wc);
    a = [1, (wc - K)/(K + wc)];
end

function [b, a] = first_order_hpf(fc, fs)
%FIRST_ORDER_HPF  Bilinear-transform equivalent of H(s)=s/(s+wc).
    wc = 2*pi*fc;
    K  = 2*fs;

    b = [K, -K] / (K + wc);
    a = [1, (wc - K)/(K + wc)];
end

function [b, a] = second_order_notch(f0, Q, fs)
%SECOND_ORDER_NOTCH  Digital notch approximation centered at f0.
%
% The SystemVerilog/schematic block is an active Twin-T notch.
% For time-domain validation, this second-order notch approximates the
% expected 60 Hz rejection and Q. For exact analog Twin-T frequency response,
% use active_twin_t_response.m.

    w0 = 2*pi*f0/fs;

    % Pole radius approximation. Higher Q -> radius closer to 1.
    r = 1 - (pi*f0)/(Q*fs);
    r = max(min(r, 0.9999), 0.70);

    b = [1, -2*cos(w0), 1];
    a = [1, -2*r*cos(w0), r^2];

    % Normalize DC gain to 1.
    H0 = sum(b) / sum(a);
    b = b / H0;
end
