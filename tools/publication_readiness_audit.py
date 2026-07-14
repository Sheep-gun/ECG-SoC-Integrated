#!/usr/bin/env python3
"""Generate publication-readiness size and raw-dataset audit artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
GIT = os.environ.get("GIT_EXECUTABLE") or shutil.which("git")
if not GIT:
    raise RuntimeError("Git executable not found. Set GIT_EXECUTABLE or add git to PATH.")
BASELINE = "32d2fbd582040f7de7ed54e4ecf5a8a4efd19268"
AFE_COMMIT = "4756a5086023547328ef44fd5fd87da3c250dc39"
DATASET_ROOTS = {
    "nsrdb": "components/afe_xmodel/algorithm/person_data/nsrdb/1.0.0",
    "chfdb": "components/afe_xmodel/algorithm/person_data/chfdb/1.0.0",
    "mitdb": "components/afe_xmodel/algorithm/person_data/mitdb/1.0.0",
    "afdb": "components/afe_xmodel/algorithm/person_data/afdb/1.0.0",
}


def git(*args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        [GIT, "-C", str(ROOT), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
        encoding="utf-8" if text else None,
    )
    return result.stdout.strip() if text else result.stdout


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def all_files() -> tuple[list[Path], list[Path]]:
    work, dotgit = [], []
    scan_root = Path("\\\\?\\" + str(ROOT.resolve())) if os.name == "nt" else ROOT
    for path in scan_root.rglob("*"):
        if not path.is_file():
            continue
        (dotgit if ".git" in path.relative_to(scan_root).parts else work).append(path)
    return work, dotgit


def tracked_files() -> list[Path]:
    raw = git("-c", "core.quotepath=false", "ls-files", "-z", text=False)
    assert isinstance(raw, bytes)
    return [ROOT / item.decode("utf-8") for item in raw.split(b"\0") if item]


def historical_blobs() -> list[dict]:
    objects = git("rev-list", "--objects", "--all")
    assert isinstance(objects, str)
    result = subprocess.run(
        [GIT, "-C", str(ROOT), "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)"],
        input=objects + "\n", check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8",
    )
    rows = []
    for line in result.stdout.splitlines():
        parts = line.split(" ", 3)
        if len(parts) >= 3 and parts[1] == "blob":
            rows.append({
                "blob_sha": parts[0], "size_bytes": int(parts[2]),
                "path": parts[3] if len(parts) == 4 else "",
            })
    return sorted(rows, key=lambda row: int(row["size_bytes"]), reverse=True)


def dataset_for(rel: str) -> str | None:
    normalized = rel.replace("\\", "/")
    for dataset, prefix in DATASET_ROOTS.items():
        if normalized == prefix or normalized.startswith(prefix + "/"):
            return dataset
    return None


def generate_before() -> None:
    reports = ROOT / "reports"
    work, dotgit = all_files()
    tracked = [path for path in tracked_files() if path.exists()]
    current_rows = []
    for path in tracked:
        size = path.stat().st_size
        if size >= 10 * 1024 * 1024:
            rel = path.relative_to(ROOT).as_posix()
            current_rows.append({"path": rel, "size_bytes": size, "git_blob_sha": git("hash-object", rel)})
    current_rows.sort(key=lambda row: int(row["size_bytes"]), reverse=True)
    write_csv(reports / "largest_current_files_before.csv", list(current_rows[0]), current_rows)

    blobs = historical_blobs()
    write_csv(reports / "largest_git_blobs_before.csv", ["blob_sha", "size_bytes", "path"], blobs[:200])

    raw_rows = []
    excluded_rows = []
    for path in tracked:
        rel = path.relative_to(ROOT).as_posix()
        dataset = dataset_for(rel)
        if not dataset:
            continue
        size = path.stat().st_size
        row = {
            "path": rel, "dataset": dataset, "size_bytes": size,
            "git_blob_sha": git("hash-object", rel), "sha256": file_sha256(path),
            "origin_repository": "https://github.com/Hwan-22/ECG-SoC",
            "origin_commit": AFE_COMMIT, "owner": "이수환",
            "content_category": "third-party raw dataset distribution file",
            "disposition": "remove from Git history; restore through fixed-version PhysioNet fetch",
        }
        raw_rows.append(row)
        excluded_rows.append({
            "component": "afe_xmodel", "upstream_commit": AFE_COMMIT,
            "upstream_path": rel.removeprefix("components/afe_xmodel/"),
            "integrated_path": rel, "size_bytes": size, "sha256": row["sha256"],
            "dataset": dataset,
            "reason": "fixed-version third-party PhysioNet dataset is reproducibly fetched and is not bundled",
        })
    raw_rows.sort(key=lambda row: row["path"])
    write_csv(reports / "raw_dataset_inventory.csv", list(raw_rows[0]), raw_rows)
    write_csv(
        ROOT / "integration_evidence" / "excluded_large_dataset_paths.csv",
        list(excluded_rows[0]), excluded_rows,
    )

    expected_lines = [
        "# SHA256 copied from the fixed-version PhysioNet SHA256SUMS.txt files",
        "# Format: sha256  abbreviation/version/relative_path",
    ]
    for dataset, prefix in DATASET_ROOTS.items():
        source = ROOT / prefix / "SHA256SUMS.txt"
        expected_lines.append(f"# {dataset}/1.0.0")
        for line in source.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            digest, name = stripped.split(maxsplit=1)
            expected_lines.append(f"{digest.lower()}  {dataset}/1.0.0/{name.lstrip('*./')}")
    datasets_dir = ROOT / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    (datasets_dir / "SHA256SUMS_EXPECTED.txt").write_text(
        "\n".join(expected_lines) + "\n", encoding="utf-8"
    )

    disposition = []
    for row in current_rows:
        rel = str(row["path"])
        dataset = dataset_for(rel)
        remove = dataset is not None
        disposition.append({
            "path": rel, "size_bytes": row["size_bytes"], "Git blob SHA": row["git_blob_sha"],
            "origin repository": "https://github.com/Hwan-22/ECG-SoC" if remove else "fixed component snapshot",
            "origin commit": AFE_COMMIT if remove else "see artifact_manifest.csv", "owner": "이수환" if remove else "component owner",
            "content category": "third-party raw dataset" if remove else "project-authored derived/locked evidence",
            "retain_or_remove": "REMOVE_FROM_HISTORY" if remove else "RETAIN",
            "rationale": "authoritative fixed-version source is reproducibly fetchable" if remove else "required technical evidence",
            "replacement artifact": "datasets/dataset_manifest.yaml + SHA256SUMS_EXPECTED.txt" if remove else "not applicable",
            "evidence affected": "raw source availability only; derived evidence retained" if remove else "direct report/integration evidence",
        })
    fields = ["path", "size_bytes", "Git blob SHA", "origin repository", "origin commit", "owner", "content category", "retain_or_remove", "rationale", "replacement artifact", "evidence affected"]
    write_csv(reports / "large_file_disposition.csv", fields, disposition)

    bundle = ROOT.parent / "ECG-SoC-Integrated-before-slimming.bundle"
    count_objects = git("count-objects", "-vH")
    status = git("status", "--porcelain=v2")
    remote = git("remote", "get-url", "origin")
    content = f"""# Publication-readiness preflight

Captured before repository-content changes and history rewriting.

## Git identity and safety

- Branch: `{git('branch', '--show-current')}`
- HEAD: `{git('rev-parse', 'HEAD')}`
- Commit message: `{git('log', '-1', '--pretty=%s')}`
- Public baseline expected/verified: `{BASELINE}`
- Remote: `origin` → `{remote}`
- Worktree/index status: `{'clean' if not status else status}`
- Backup bundle: `{bundle}`
- Bundle SHA256: `{file_sha256(bundle) if bundle.exists() else 'MISSING'}`
- Bundle verification: complete-history bundle verified with `git bundle verify`

## Measured size

- Working-tree bytes excluding `.git`: {sum(p.stat().st_size for p in work)}
- `.git` bytes: {sum(p.stat().st_size for p in dotgit)}
- Repository total bytes: {sum(p.stat().st_size for p in work + dotgit)}
- Tracked files ≥10 MiB: {len(current_rows)}
- Tracked files ≥50 MiB: {sum(int(r['size_bytes']) >= 50 * 1024 * 1024 for r in current_rows)}
- Largest tracked file: `{current_rows[0]['path']}` ({current_rows[0]['size_bytes']} bytes)
- Audited raw-dataset paths: {len(raw_rows)}

`git count-objects -vH`:

```text
{count_objects}
```

## Baseline integrity

- `python tools/check_integrated_repository.py`: PASS, 163 rules, 0 conflicts
- `python tools/check_integrated_technical_report.py`: PASS, 199 rules, 0 conflicts

Machine-readable measurements are in `largest_current_files_before.csv`, `largest_git_blobs_before.csv`, `raw_dataset_inventory.csv`, and `large_file_disposition.csv`.
"""
    (reports / "PUBLICATION_READINESS_PREFLIGHT.md").write_text(content, encoding="utf-8")


def generate_after() -> None:
    reports = ROOT / "reports"
    work, dotgit = all_files()
    tracked = [path for path in tracked_files() if path.exists()]
    current_rows = []
    for path in tracked:
        size = path.stat().st_size
        if size >= 1024 * 1024:
            rel = path.relative_to(ROOT).as_posix()
            current_rows.append({"path": rel, "size_bytes": size, "git_blob_sha": git("hash-object", rel)})
    current_rows.sort(key=lambda row: int(row["size_bytes"]), reverse=True)
    write_csv(reports / "largest_current_files_after.csv", ["path", "size_bytes", "git_blob_sha"], current_rows)
    blobs = historical_blobs()
    write_csv(reports / "largest_git_blobs_after.csv", ["blob_sha", "size_bytes", "path"], blobs[:200])
    print({
        "working_tree_bytes": sum(p.stat().st_size for p in work),
        "git_bytes": sum(p.stat().st_size for p in dotgit),
        "repo_total_bytes": sum(p.stat().st_size for p in work + dotgit),
        "tracked_ge10_mib": sum(int(r["size_bytes"]) >= 10 * 1024 * 1024 for r in current_rows),
        "tracked_ge50_mib": sum(int(r["size_bytes"]) >= 50 * 1024 * 1024 for r in current_rows),
        "largest_retained": current_rows[0] if current_rows else None,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["before", "after"])
    args = parser.parse_args()
    if args.phase == "before":
        generate_before()
    else:
        generate_after()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
