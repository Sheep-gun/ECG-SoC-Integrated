# Publication-readiness preflight

Captured before repository-content changes and history rewriting.

## Git identity and safety

- Branch: `main`
- HEAD: `32d2fbd582040f7de7ed54e4ecf5a8a4efd19268`
- Commit message: `Add integrated Korean technical report manuscript`
- Public baseline expected/verified: `32d2fbd582040f7de7ed54e4ecf5a8a4efd19268`
- Remote: `origin` → `https://github.com/Sheep-gun/ECG-SoC-Integrated.git`
- Worktree/index status: `? datasets/
? integration_evidence/excluded_large_dataset_paths.csv
? reports/PUBLICATION_READINESS_PREFLIGHT.md
? reports/large_file_disposition.csv
? reports/largest_current_files_before.csv
? reports/largest_git_blobs_before.csv
? reports/raw_dataset_inventory.csv
? tools/publication_readiness_audit.py`
- Backup bundle: `<LOCAL_BACKUP_BUNDLE>`
- Bundle SHA256: `6601aa18474939d0c659afae6219e7e7371287dcea7acf12171d169fbb929d1c`
- Bundle verification: complete-history bundle verified with `git bundle verify`

## Measured size

- Working-tree bytes excluding `.git`: 2307174104
- `.git` bytes: 1535086190
- Repository total bytes: 3842260294
- Tracked files ≥10 MiB: 56
- Tracked files ≥50 MiB: 15
- Largest tracked file: `components/afe_xmodel/algorithm/person_data/chfdb/1.0.0/chf03.dat` (53996544 bytes)
- Audited raw-dataset paths: 977

`git count-objects -vH`:

```text
count: 1864
size: 1.42 GiB
in-pack: 0
packs: 0
size-pack: 0 bytes
prune-packable: 0
garbage: 0
size-garbage: 0 bytes
```

## Baseline integrity

- `python tools/check_integrated_repository.py`: PASS, 163 rules, 0 conflicts
- `python tools/check_integrated_technical_report.py`: PASS, 199 rules, 0 conflicts

Machine-readable measurements are in `largest_current_files_before.csv`, `largest_git_blobs_before.csv`, `raw_dataset_inventory.csv`, and `large_file_disposition.csv`.
