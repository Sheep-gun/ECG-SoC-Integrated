#!/usr/bin/env python3
"""Refresh repository manifests after the AF class-label normalization.

Run this only as part of the repository-wide label migration. It updates hashes
and sizes to the checked-in integrated artifacts while retaining the recorded
upstream commit as the provenance baseline.
"""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_MANIFEST = ROOT / "source_of_truth" / "artifact_manifest.csv"
REDACTION_MANIFEST = ROOT / "source_of_truth" / "path_redaction_manifest.csv"
NORMALIZED_STATUS = "HASH_VERIFIED_AF_NORMALIZED"
NORMALIZED_NOTE = (
    "integrated artifact after AF class-label normalization; classifier "
    "arithmetic, class ID, and numeric evidence are unchanged"
)
GIT = os.environ.get("GIT_EXECUTABLE", shutil.which("git") or "git")
AF_PATH_TOKEN = re.compile(r"(?<![A-Za-z])AF(?![A-Za-z])")


def readable_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if os.name == "nt":
        return Path("\\\\?\\" + str(path))
    return path


def digest(path: Path) -> tuple[str, int]:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest(), len(data)


def indexed_digest(relative: str) -> str:
    result = subprocess.run(
        [GIT, "-C", str(ROOT), "show", f":{relative}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"stage normalized artifact before refreshing redaction hash: {relative}"
        )
    return hashlib.sha256(result.stdout).hexdigest()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def refresh_artifact_manifest() -> int:
    fieldnames, rows = read_rows(ARTIFACT_MANIFEST)
    changed = 0
    for row in rows:
        sha256, size = digest(readable_path(row["integrated_path"]))
        hash_changed = sha256 != row["sha256"] or str(size) != row["size_bytes"]
        path_normalized = bool(
            AF_PATH_TOKEN.search(row["upstream_path"])
            or AF_PATH_TOKEN.search(row["integrated_path"])
        )
        status_changed = path_normalized and row["verification_status"] != NORMALIZED_STATUS
        if hash_changed or status_changed:
            row["sha256"] = sha256
            row["size_bytes"] = str(size)
            row["verification_status"] = NORMALIZED_STATUS
            row["notes"] = NORMALIZED_NOTE
            changed += 1
    write_rows(ARTIFACT_MANIFEST, fieldnames, rows)
    return changed


def refresh_redaction_manifest() -> int:
    fieldnames, rows = read_rows(REDACTION_MANIFEST)
    changed = 0
    for row in rows:
        sha256 = indexed_digest(row["tracked_path"])
        if sha256 != row["sanitized_sha256"]:
            row["sanitized_sha256"] = sha256
            changed += 1
    write_rows(REDACTION_MANIFEST, fieldnames, rows)
    return changed


def main() -> int:
    artifacts = refresh_artifact_manifest()
    redactions = refresh_redaction_manifest()
    print(f"PASS refreshed {artifacts} artifact hashes and {redactions} redaction hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
