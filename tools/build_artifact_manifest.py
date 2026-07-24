#!/usr/bin/env python3
"""Build a deterministic SHA-256 manifest for the curated public workspace."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "project_registry" / "artifact_manifest.csv"
EXCLUDED_PARTS = {".git", "tmp", "__pycache__", ".pytest_cache", ".mypy_cache"}


def category(path: Path) -> str:
    top = path.parts[0] if path.parts else "root"
    return {
        "analysis": "feature_analysis",
        "datasets": "dataset_manifest_or_derived_input",
        "design": "design_source_or_fixed_result",
        "docs": "technical_documentation",
        "figures": "publication_figure",
        "models": "reference_model_or_benchmark",
        "project_registry": "registry",
        "reports": "integrated_report",
        "tables": "publication_table",
        "tools": "reproduction_tool",
        "verification": "verification_evidence",
        "vivado": "vivado_project",
    }.get(top, "repository_control")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    paths: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path == OUTPUT:
            continue
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        paths.append(rel)

    paths.sort(key=lambda p: p.as_posix().casefold())
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["artifact_id", "path", "category", "size_bytes", "sha256"])
        for index, rel in enumerate(paths, 1):
            absolute = ROOT / rel
            writer.writerow([
                f"ART-{index:05d}",
                rel.as_posix(),
                category(rel),
                absolute.stat().st_size,
                sha256(absolute),
            ])

    print(f"ARTIFACT_MANIFEST: PASS ({len(paths)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
