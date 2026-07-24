function verify_reference_vector_manifest(manifest_file)
%VERIFY_REFERENCE_VECTOR_MANIFEST Verify byte counts and SHA256 hashes.
%
% This script fails with MATLAB error when any manifest entry is missing or
% does not match. It is intentionally fail-fast for integration reproducibility.

    if nargin < 1 || isempty(manifest_file)
        manifest_file = fullfile('reference_vectors', 'reference_vector_manifest.csv');
    end

    if ~exist(manifest_file, 'file')
        error('verify_reference_vector_manifest:ManifestMissing', ...
              'Manifest file not found: %s', manifest_file);
    end

    T = readtable(manifest_file, 'TextType', 'string');
    required = {'relative_path','bytes','sha256'};
    for k = 1:numel(required)
        if ~any(strcmp(T.Properties.VariableNames, required{k}))
            error('verify_reference_vector_manifest:BadManifest', ...
                  'Manifest missing column: %s', required{k});
        end
    end

    failures = strings(0,1);

    for i = 1:height(T)
        rel = char(T.relative_path(i));
        if startsWith(rel, 'reference_vectors/')
            rel_local = rel(length('reference_vectors/')+1:end);
            f = fullfile('reference_vectors', rel_local);
        else
            f = rel;
        end

        if ~exist(f, 'file')
            failures(end+1,1) = "missing file: " + string(rel); %#ok<AGROW>
            continue;
        end

        info = dir(f);
        actual_bytes = info.bytes;
        expected_bytes = double(T.bytes(i));
        if actual_bytes ~= expected_bytes
            failures(end+1,1) = sprintf("byte mismatch: %s expected=%d actual=%d", rel, expected_bytes, actual_bytes); %#ok<AGROW>
        end

        actual_sha = sha256_file_local(f);
        expected_sha = lower(char(T.sha256(i)));
        if ~strcmpi(actual_sha, expected_sha)
            failures(end+1,1) = sprintf("sha256 mismatch: %s expected=%s actual=%s", rel, expected_sha, actual_sha); %#ok<AGROW>
        end
    end

    if ~isempty(failures)
        fprintf(2, 'Reference vector manifest verification failed:\n');
        for i = 1:numel(failures)
            fprintf(2, '  - %s\n', failures(i));
        end
        error('verify_reference_vector_manifest:Mismatch', ...
              '%d manifest entries failed verification.', numel(failures));
    end

    fprintf('Reference vector manifest verification passed: %d files checked.\n', height(T));
end

function h = sha256_file_local(file)
    md = java.security.MessageDigest.getInstance('SHA-256');
    fid = fopen(file, 'rb');
    if fid < 0
        error('sha256_file_local:OpenFailed', 'Cannot open %s', file);
    end
    cleaner = onCleanup(@() fclose(fid));
    while true
        data = fread(fid, 1024*1024, '*uint8');
        if isempty(data)
            break;
        end
        md.update(data);
    end
    hash = typecast(md.digest(), 'uint8');
    h = lower(reshape(dec2hex(hash)', 1, []));
end
