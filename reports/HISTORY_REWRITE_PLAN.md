# Git history rewrite plan

## Safety baseline

- Pre-rewrite public baseline: `32d2fbd582040f7de7ed54e4ecf5a8a4efd19268`
- Branch: `main`
- Remote before maintenance: `origin` → `https://github.com/Sheep-gun/ECG-SoC-Integrated.git`
- Backup bundle: `C:\Users\YangGeon\SNN ECG Classifier\ECG-SoC-Integrated-before-slimming.bundle`
- Bundle SHA256: `6601AA18474939D0C659AFAE6219E7E7371287DCEA7ACF12171D169FBB929D1C`
- Bundle verification: complete history, `git bundle verify` PASS
- Force push in this task: forbidden

## Exact removal rules

Only these audited upstream-export prefixes are removed from every reachable commit:

```text
components/afe_xmodel/algorithm/person_data/nsrdb/1.0.0/
components/afe_xmodel/algorithm/person_data/chfdb/1.0.0/
components/afe_xmodel/algorithm/person_data/mitdb/1.0.0/
components/afe_xmodel/algorithm/person_data/afdb/1.0.0/
```

The complete 977-path pre-rewrite inventory, size, Git blob SHA and SHA256 is in `raw_dataset_inventory.csv` and `integration_evidence/excluded_large_dataset_paths.csv`. No wildcard-by-extension rule is used.

## Retention rules

Retain project-authored source, preprocessing code, selected-record/split manifests, locked `.mem` input, derived result CSV/JSON, integration comparison, board-replay evidence, compact reference vectors, figures and reports. In particular, raw-origin provenance does not make a derived/locked artifact a removal target.

## Tool and sequence

1. Complete and commit content/provenance changes, with a clean worktree.
2. Run `git filter-repo --force --invert-paths` with the four exact `--path` prefixes above.
3. Restore the removed `origin` configuration locally if the tool removes it; do not push.
4. Expire reflogs and run garbage collection so removed blobs are absent locally.
5. Verify each prefix is absent from `git rev-list --objects --all`, no raw dataset is tracked, retained artifact hashes pass, manuscript and benchmark placeholder remain, and both checkers pass.
6. Record before/after sizes and rewritten HEAD.

History rewriting changes commit IDs for all affected commits. The backup bundle is never modified or deleted.
