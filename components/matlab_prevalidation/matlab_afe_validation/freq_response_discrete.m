function [f, H] = freq_response_discrete(b, a, fs, freq_or_nfft)
%FREQ_RESPONSE_DISCRETE  Toolbox-free discrete-time frequency response.
%
% Usage:
%   [f,H] = freq_response_discrete(b,a,fs,nfft)
%   [f,H] = freq_response_discrete(b,a,fs,freq_vector)
%
% The second form is used when a log-spaced frequency vector is needed
% for plotting.  This keeps the output order compatible with older calls
% that expect [f,H].

    if nargin < 4 || isempty(freq_or_nfft)
        freq_or_nfft = 8192;
    end

    if isscalar(freq_or_nfft)
        nfft = freq_or_nfft;
        f = linspace(0, fs/2, nfft).';
    else
        f = freq_or_nfft(:);
    end

    z = exp(1j*2*pi*f/fs);

    % H(z) = (b0 + b1 z^-1 + ...)/(a0 + a1 z^-1 + ...)
    num = zeros(size(z));
    den = zeros(size(z));

    for k = 1:length(b)
        num = num + b(k) .* z.^(-(k-1));
    end
    for k = 1:length(a)
        den = den + a(k) .* z.^(-(k-1));
    end

    H = num ./ den;
end
