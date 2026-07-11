#!/usr/bin/env python3
"""Recreate curated fixed-component snapshots from local Git objects.

The default safety policy rejects staged or modified tracked files. An explicit
component-name exception exists only for a concurrently edited benchmark
worktree; it does not change the exported bytes because `git archive` reads the
fixed commit object rather than the worktree.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
ANALOG_SEARCH_ROOT = Path(r"C:\Users\YangGeon\Desktop\Analog")
GIT = os.environ.get(
    "GIT_EXECUTABLE",
    shutil.which("git")
    or r"C:\Users\YangGeon\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe",
)

COMPONENTS = {
    "matlab_prevalidation": {
        "origin": "https://github.com/ferocious-kiwi/ECG-SoC-MATLAB-AFE-ADC-Prevalidation",
        "commit": "907f7e1f081a9d6a5703a32095d962143315a192",
        "owner": "서민우",
        "search": True,
    },
    "afe_xmodel": {
        "origin": "https://github.com/Hwan-22/ECG-SoC",
        "commit": "4756a5086023547328ef44fd5fd87da3c250dc39",
        "owner": "이수환",
        "search": True,
    },
    "digital_accelerator": {
        "origin": "https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier",
        "commit": "c6b80de19cdcad5b7e43fe7835588b629d847f75",
        "owner": "양건",
        "path": ROOT.parent,
        "search": False,
    },
}

EXCLUDED_PREFIXES = {
    "afe_xmodel": {
        "docs/submission/": "contest notice/application forms are forbidden in the integrated Git repository",
        "algorithm/person_data/nsrdb/1.0.0/": "fixed-version third-party PhysioNet raw dataset is restored through datasets/dataset_manifest.yaml",
        "algorithm/person_data/chfdb/1.0.0/": "fixed-version third-party PhysioNet raw dataset is restored through datasets/dataset_manifest.yaml",
        "algorithm/person_data/mitdb/1.0.0/": "fixed-version third-party PhysioNet raw dataset is restored through datasets/dataset_manifest.yaml",
        "algorithm/person_data/afdb/1.0.0/": "fixed-version third-party PhysioNet raw dataset is restored through datasets/dataset_manifest.yaml",
    },
}


def run_git(repo: Path, *args: str, binary: bool = False):
    result = subprocess.run(
        [GIT, "-C", str(repo), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
    )
    return result.stdout if binary else result.stdout.strip()


def normalize_origin(value: str) -> str:
    value = value.strip().replace("\\", "/")
    if value.endswith(".git"):
        value = value[:-4]
    return value.rstrip("/").lower()


def discover_repositories() -> dict[str, Path]:
    candidates: list[Path] = []
    for git_dir in ANALOG_SEARCH_ROOT.rglob(".git"):
        if git_dir.is_dir():
            candidates.append(git_dir.parent.resolve())

    found: dict[str, Path] = {}
    for component, spec in COMPONENTS.items():
        if spec.get("search"):
            matches = []
            for repo in candidates:
                try:
                    origin = run_git(repo, "remote", "get-url", "origin")
                except subprocess.CalledProcessError:
                    continue
                if normalize_origin(origin) == normalize_origin(str(spec["origin"])):
                    matches.append(repo)
            if len(matches) != 1:
                raise RuntimeError(
                    f"{component}: expected exactly one origin match, found {len(matches)}: {matches}"
                )
            found[component] = matches[0]
        else:
            repo = Path(spec["path"]).resolve()
            origin = run_git(repo, "remote", "get-url", "origin")
            if normalize_origin(origin) != normalize_origin(str(spec["origin"])):
                raise RuntimeError(f"{component}: origin mismatch: {origin}")
            found[component] = repo
    return found


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".sv": "SystemVerilog source",
        ".svh": "SystemVerilog header",
        ".v": "Verilog source",
        ".vhd": "VHDL source",
        ".m": "MATLAB source",
        ".py": "Python source",
        ".c": "C source",
        ".h": "C/C++ header",
        ".csv": "tabular evidence",
        ".json": "structured evidence",
        ".yaml": "structured metadata",
        ".yml": "structured metadata",
        ".md": "documentation",
        ".txt": "text/vector artifact",
        ".mem": "memory/vector artifact",
        ".coe": "memory initialization artifact",
        ".xdc": "FPGA constraints",
        ".tcl": "tool automation",
        ".xml": "IP/tool metadata",
        ".xci": "Vivado IP metadata",
        ".png": "figure",
        ".pdf": "report artifact",
    }.get(suffix, "component artifact")


def exclusion_reason(component: str, member_name: str) -> str | None:
    normalized = PurePosixPath(member_name).as_posix()
    for prefix, reason in EXCLUDED_PREFIXES.get(component, {}).items():
        if normalized.startswith(prefix):
            return reason
    if PurePosixPath(normalized).name.startswith("~$"):
        return "temporary Office lock file is not intentional technical evidence"
    return None


def safe_extract_tar(component: str, payload: bytes, destination: Path) -> list[dict]:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    extended_destination = "\\\\?\\" + str(root)
    excluded: list[dict] = []
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if os.path.commonpath([str(root), str(target)]) != str(root):
                raise RuntimeError(f"unsafe archive path: {member.name}")
            if member.issym() or member.islnk():
                raise RuntimeError(f"links are not imported: {member.name}")
        for member in archive.getmembers():
            reason = exclusion_reason(component, member.name)
            if reason and member.isfile():
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError(f"cannot read excluded member: {member.name}")
                with source:
                    digest = hashlib.sha256(source.read()).hexdigest()
                excluded.append({
                    "component": component,
                    "upstream_commit": COMPONENTS[component]["commit"],
                    "upstream_path": PurePosixPath(member.name).as_posix(),
                    "size_bytes": member.size,
                    "sha256": digest,
                    "reason": reason,
                })
                continue
            if reason and member.isdir():
                continue
            parts = PurePosixPath(member.name).parts
            target_name = os.path.join(extended_destination, *parts)
            if member.isdir():
                os.makedirs(target_name, exist_ok=True)
                continue
            if not member.isfile():
                raise RuntimeError(f"unsupported archive member: {member.name}")
            os.makedirs(os.path.dirname(target_name), exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"cannot read archive member: {member.name}")
            with source, open(target_name, "wb") as output:
                shutil.copyfileobj(source, output)
    return excluded


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree("\\\\?\\" + str(path.resolve()))


def restore_exact_git_blobs(component: str, repo: Path, destination: Path, excluded: list[dict]) -> None:
    """Replace archive-converted bytes and exclusion hashes with exact Git blobs."""
    commit = COMPONENTS[component]["commit"]
    for path in destination.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(destination).as_posix()
        payload = run_git(repo, "show", f"{commit}:{rel}", binary=True)
        path.write_bytes(payload)
    for row in excluded:
        if row["component"] != component:
            continue
        payload = run_git(repo, "show", f"{commit}:{row['upstream_path']}", binary=True)
        row["size_bytes"] = len(payload)
        row["sha256"] = hashlib.sha256(payload).hexdigest()


def status_snapshot(component: str, repo: Path, spec: dict) -> dict:
    porcelain = run_git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    tracked = run_git(repo, "status", "--porcelain=v1", "--untracked-files=no")
    return {
        "component": component,
        "repository_root": str(repo),
        "origin": run_git(repo, "remote", "get-url", "origin"),
        "active_branch": run_git(repo, "branch", "--show-current"),
        "active_head": run_git(repo, "rev-parse", "HEAD"),
        "fixed_imported_commit": spec["commit"],
        "status_porcelain": porcelain.splitlines() if porcelain else [],
        "tracked_status": tracked.splitlines() if tracked else [],
        "untracked_paths": [line[3:] for line in porcelain.splitlines() if line.startswith("?? ")],
    }


def write_manifest() -> None:
    out = ROOT / "source_of_truth" / "artifact_manifest.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "artifact_id", "component", "owner", "upstream_repository",
        "upstream_commit", "upstream_path", "integrated_path", "sha256",
        "size_bytes", "artifact_type", "claim_supported", "report_section",
        "verification_status", "notes",
    ]
    rows = []
    artifact_id = 1
    for component, spec in COMPONENTS.items():
        ordinary_base = ROOT / "components" / component
        base = Path("\\\\?\\" + str(ordinary_base.resolve()))
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            rel = path.relative_to(base).as_posix()
            data = path.read_bytes()
            rows.append({
                "artifact_id": f"ART-{artifact_id:05d}",
                "component": component,
                "owner": spec["owner"],
                "upstream_repository": spec["origin"],
                "upstream_commit": spec["commit"],
                "upstream_path": rel,
                "integrated_path": f"components/{component}/{rel}",
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "artifact_type": classify(path),
                "claim_supported": "component snapshot provenance; see claim registry for promoted claims",
                "report_section": "component evidence as mapped by REPORT_EVIDENCE_MAP_KR.md",
                "verification_status": "HASH_VERIFIED_CURATED_EXPORT",
                "notes": "retained byte content exported from fixed Git commit; intentionally omitted paths are in exclusion registries",
            })
            artifact_id += 1
    with out.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--allow-dirty-tracked",
        action="append",
        default=[],
        choices=sorted(COMPONENTS),
        help="Explicit, audited exception for a concurrent worktree; fixed Git objects are still exported.",
    )
    args = parser.parse_args()
    repos = discover_repositories()
    before = []
    excluded_rows: list[dict] = []
    for component, repo in repos.items():
        spec = COMPONENTS[component]
        if normalize_origin(run_git(repo, "remote", "get-url", "origin")) != normalize_origin(str(spec["origin"])):
            raise RuntimeError(f"{component}: origin mismatch")
        run_git(repo, "cat-file", "-e", f"{spec['commit']}^{{commit}}")
        state = status_snapshot(component, repo, spec)
        if state["tracked_status"] and component not in args.allow_dirty_tracked:
            raise RuntimeError(f"{component}: tracked worktree/index is not clean: {state['tracked_status']}")
        state["dirty_tracked_exception"] = component in args.allow_dirty_tracked
        before.append(state)

    evidence = ROOT / "integration_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    payload = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "fixed-commit git archive; worktree bytes are never imported",
        "repositories": before,
    }
    (evidence / "upstream_status_before.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for component, repo in repos.items():
        target = ROOT / "components" / component
        remove_tree(target)
        archive = run_git(repo, "archive", "--format=tar", COMPONENTS[component]["commit"], binary=True)
        component_excluded = safe_extract_tar(component, archive, target)
        restore_exact_git_blobs(component, repo, target, component_excluded)
        excluded_rows.extend(component_excluded)

    excluded_path = evidence / "excluded_upstream_paths.csv"
    with excluded_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["component", "upstream_commit", "upstream_path", "size_bytes", "sha256", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(excluded_rows)

    large_dataset_rows = []
    for row in excluded_rows:
        if "PhysioNet raw dataset" not in row["reason"]:
            continue
        upstream_path = row["upstream_path"]
        dataset = next(
            name for name in ("nsrdb", "chfdb", "mitdb", "afdb")
            if f"/person_data/{name}/" in f"/{upstream_path}"
        )
        large_dataset_rows.append({
            **row,
            "integrated_path": f"components/{row['component']}/{upstream_path}",
            "dataset": dataset,
        })
    large_path = evidence / "excluded_large_dataset_paths.csv"
    with large_path.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["component", "upstream_commit", "upstream_path", "integrated_path", "size_bytes", "sha256", "dataset", "reason"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(large_dataset_rows)

    write_manifest()
    print(json.dumps({k: str(v) for k, v in repos.items()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
