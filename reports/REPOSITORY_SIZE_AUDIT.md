# Repository size and raw-data audit

## Pre-rewrite measurement

- Working tree excluding `.git`: 2,307,174,104 bytes
- `.git` objects/metadata: 1,535,086,190 bytes
- Total local repository: 3,842,260,294 bytes
- `git count-objects -vH`: 1,864 loose objects, 1.42 GiB
- Tracked files ≥10 MiB: 56
- Tracked files ≥50 MiB: 15
- Largest tracked files: CHFDB `.dat` records, maximum 53,996,544 bytes
- Audited third-party raw paths: 977

The four raw directory groups total 2,165,559,918 bytes in the working tree: nsrdb 610,011,100; chfdb 810,987,944; mitdb 109,191,712; afdb 635,369,162 bytes. These are authoritative fixed-version PhysioNet distribution files, not project-authored evidence.

## Disposition

- Remove from working tree and reachable Git history: the four exact versioned PhysioNet directory prefixes in `HISTORY_REWRITE_PLAN.md`.
- Replace source availability with `datasets/dataset_manifest.yaml`, 1,025 expected official SHA256 entries, resume-capable fetch, read-only verification, license/citation documentation and exclusion registries.
- Retain derived/locked `.mem`, evaluation CSV/JSON, final metrics, XMODEL/RTL comparisons and board-replay evidence.

Per-file decisions are in `raw_dataset_inventory.csv`, `large_file_disposition.csv`, `largest_current_files_before.csv` and `largest_git_blobs_before.csv`.

## Post-rewrite measurement

- Working tree excluding `.git`: 140,346,925 bytes
- `.git`: 48,243,693 bytes
- Total: 188,590,618 bytes
- Reachable objects: one 45.83 MiB pack
- Tracked files ≥10 MiB: 0
- Tracked files ≥50 MiB: 0
- Largest retained file/blob: 7,514,904-byte project-derived MATLAB stage-output CSV
- Raw-data prefix matches in reachable history: 0

The detailed result and percentage reduction are in `HISTORY_REWRITE_RESULT.md`; machine-readable lists are `largest_current_files_after.csv` and `largest_git_blobs_after.csv`.
