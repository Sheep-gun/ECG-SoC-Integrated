# Integration method

## Scope

The integrated repository is an independent nested Git repository. It imports three fixed upstream commits as curated read-only component snapshots and authors integration metadata, technical narratives, figures, tables, and integrity tools. Retained imported files are byte-identical to fixed upstream objects, while registered third-party raw datasets, submission/private material and temporary files are omitted.

## Discovery and safety

MATLAB and XMODEL clones are discovered below the configured analog search root by normalized `origin` URL. The digital repository is identified by its own origin. Exact machine-local paths are confined to `source_of_truth/upstream_commits.yaml` and audit JSON rather than final-facing prose. For each source the integration records current branch, current HEAD, fixed import SHA, tracked status, and untracked paths.

The digital benchmark branch was active during integration. The user explicitly authorized concurrent work because the export reads fixed commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`, not the current worktree. The concurrent status is preserved in `integration_evidence/upstream_status_before.json`. No upstream checkout, switch, reset, clean, stash, pull, merge, add, or commit is performed.

## Commit-pinned export

`tools/import_upstream_repositories.py` validates origin and fixed commit, then executes `git archive --format=tar <fixed_commit>`. It applies the deterministic exclusion policy, extracts retained regular files into component-specific directories, rejects links/path traversal, and computes SHA256 for every retained imported file.

The default policy rejects modified or staged tracked files. `--allow-dirty-tracked digital_accelerator` is an explicit audited exception for this integration because concurrent benchmark edits were authorized; it does not alter export bytes.

## Intentional exclusions

The XMODEL fixed commit tracked contest notice/application material, one temporary Office lock file, and copies of four fixed-version PhysioNet databases. These paths are excluded because private/submission material is forbidden and authoritative raw datasets are reproducibly downloadable. Every omitted path, size, SHA256 and reason is recorded in `integration_evidence/excluded_upstream_paths.csv`; raw-dataset paths are duplicated in the focused `excluded_large_dataset_paths.csv`. Dataset versions, citations and expected hashes are in `datasets/`. Derived locked `.mem`, evaluation CSV, board replay and integration evidence remain retained.

## Manifest and source of truth

`artifact_manifest.csv` maps each retained imported file to component, owner, origin, fixed commit, upstream path, integrated path, SHA256 and size. It must be interpreted together with both exclusion registries. `build_global_metrics.py` reads pinned JSON/CSV/report artifacts, asserts expected values and writes a metric registry in YAML-compatible JSON syntax. Benchmark fields remain null.

## Nested repository handling

The parent digital repository locally ignores `/ECG-SoC-Integrated/` using `.git/info/exclude`. The tracked parent `.gitignore` is not changed and the integrated repository is never added to the parent index.

## Verification

`tools/check_integrated_repository.py` verifies origins/commits, component hashes, required structure, source-of-truth consistency, measured-board timing, Vivado-estimated power boundaries, claim boundaries, privacy controls, nested-repository isolation and upstream before/after invariants. Its final report is `reports/integrated_repository_check.md`.
