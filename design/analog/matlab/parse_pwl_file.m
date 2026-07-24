function data = parse_pwl_file(filename)
%PARSE_PWL_FILE  Read ECG PWL text as [time_s, voltage_V].
%
% Supported formats:
%   1) Plain numeric two-column file
%        0.000000   -0.000145
%        0.002778   -0.000145
%
%   2) LTspice-style PWL pairs with SI suffixes
%        0      -145u
%        2.778m -145u
%
%   3) Inline or multi-line PWL expression
%        PWL(0 -145u 2.778m -145u 5.556m -145u)
%
% Unit convention:
%   time is converted to seconds, voltage is converted to volts.
%   SPICE suffix rule is used: m = milli, u = micro, n = nano, etc.

    txt = fileread(filename);

    % Remove common line comments. Keep data before comment markers.
    lines = regexp(txt, '\r\n|\n|\r', 'split');
    cleaned = strings(0,1);

    for i = 1:numel(lines)
        line = strtrim(lines{i});
        if line == ""
            continue;
        end

        % Full-line LTspice/SPICE comments often start with *.
        if startsWith(line, '*')
            continue;
        end

        % Drop inline comments after ; or #.
        line = regexprep(line, '[;#].*$', '');

        % LTspice continuation lines may start with +.
        line = regexprep(line, '^\s*\+\s*', '');

        if strlength(strtrim(line)) > 0
            cleaned(end+1,1) = string(line); %#ok<AGROW>
        end
    end

    txt = strjoin(cleaned, newline);

    % Replace separators and PWL syntax with spaces.
    txt = regexprep(txt, '(?i)PWL', ' ');
    txt = regexprep(txt, '[(),=\[\]{}]', ' ');
    txt = regexprep(txt, '"', ' ');

    tokens = regexp(txt, '\S+', 'match');
    values = [];

    for i = 1:numel(tokens)
        [ok, val] = parse_spice_number(tokens{i});
        if ok
            values(end+1,1) = val; %#ok<AGROW>
        end
    end

    if isempty(values)
        error('parse_pwl_file:NoNumericData', ...
              'No numeric PWL data found in %s', filename);
    end

    if mod(numel(values), 2) ~= 0
        warning('parse_pwl_file:OddTokenCount', ...
                'Odd number of numeric tokens found. Last token is ignored.');
        values = values(1:end-1);
    end

    data = reshape(values, 2, []).';

    % Remove rows with non-finite values.
    data = data(all(isfinite(data), 2), :);

    if size(data,1) < 2
        error('parse_pwl_file:TooShort', ...
              'PWL data must contain at least two time-voltage pairs.');
    end

    % Sort and remove duplicated time points while preserving first value.
    [~, order] = sort(data(:,1), 'ascend');
    data = data(order, :);
    [~, unique_idx] = unique(data(:,1), 'stable');
    data = data(unique_idx, :);
end

function [ok, val] = parse_spice_number(tok)
%PARSE_SPICE_NUMBER  Parse a numeric token with optional SPICE suffix.

    ok = false;
    val = NaN;

    tok = strtrim(tok);
    tok = regexprep(tok, '^[,;:]+|[,;:]+$', '');

    % Strict full-token numeric match. This prevents tokens such as V1 or n001
    % from being misread as numbers.
    expr = ['^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)' ...
            '([a-zA-Zµ]*)$'];
    m = regexp(tok, expr, 'tokens', 'once');

    if isempty(m)
        return;
    end

    base = str2double(m{1});
    if isnan(base)
        return;
    end

    suffix = lower(strrep(m{2}, 'µ', 'u'));

    switch suffix
        case {''}
            scale = 1;
        case {'t'}
            scale = 1e12;
        case {'g'}
            scale = 1e9;
        case {'meg'}
            scale = 1e6;
        case {'k'}
            scale = 1e3;
        case {'m'}
            scale = 1e-3;
        case {'u'}
            scale = 1e-6;
        case {'n'}
            scale = 1e-9;
        case {'p'}
            scale = 1e-12;
        case {'f'}
            scale = 1e-15;
        otherwise
            % Unknown suffix means this is probably not a numeric data token.
            return;
    end

    val = base * scale;
    ok = true;
end
