# Integration method

## Scope

The integrated repository is an independent nested Git repository. It imports three fixed upstream commits as read-only component snapshots and authors only integration metadata, technical narratives, figures, tables, and integrity tools.

## Discovery and safety

MATLAB and XMODEL clones are discovered below `C:/Users/YangGeon/Desktop/Analog` by normalized `origin` URL. The digital repository is identified by its own origin. For each source the integration records current branch, current HEAD, fixed import SHA, tracked status, and untracked paths.

The digital benchmark branch was active during integration. The user explicitly authorized concurrent work because the export reads fixed commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`, not the current worktree. The concurrent status is preserved in `integration_evidence/upstream_status_before.json`. No upstream checkout, switch, reset, clean, stash, pull, merge, add, or commit is performed.

## Commit-pinned export

`tools/import_upstream_repositories.py` validates origin and fixed commit, then executes `git archive --format=tar <fixed_commit>`. It extracts regular tracked files into component-specific directories, rejects links/path traversal, and computes SHA256 for every imported file.

The default policy rejects modified or staged tracked files. `--allow-dirty-tracked digital_accelerator` is an explicit audited exception for this integration because concurrent benchmark edits were authorized; it does not alter export bytes.

## Intentional exclusions

The XMODEL fixed commit tracked three contest notice/application files and one temporary Office lock file. They are excluded because the integration goal forbids application/private material and temporary products. Their upstream paths, sizes, SHA256 and reasons remain recorded in `integration_evidence/excluded_upstream_paths.csv`. No other tracked technical artifact is intentionally omitted.

## Manifest and source of truth

`artifact_manifest.csv` maps each imported file to component, owner, origin, fixed commit, upstream path, integrated path, SHA256 and size. `build_global_metrics.py` reads pinned JSON/CSV/report artifacts, asserts expected values and writes a metric registry in YAML-compatible JSON syntax. Benchmark fields remain null.

## Nested repository handling

The parent digital repository locally ignores `/ECG-SoC-Integrated/` using `.git/info/exclude`. The tracked parent `.gitignore` is not changed and the integrated repository is never added to the parent index.

## Verification

`tools/check_integrated_repository.py` verifies origins/commits, component hashes, required structure, source-of-truth consistency, benchmark nulls, claim boundaries, privacy controls, nested-repository isolation and upstream before/after invariants. Its final report is `reports/integrated_repository_check.md`.
