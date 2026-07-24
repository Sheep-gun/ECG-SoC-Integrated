#!/usr/bin/env python3
"""Read-only verification of fixed-version PhysioNet datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets" / "dataset_manifest.yaml"
HASHES = ROOT / "datasets" / "SHA256SUMS_EXPECTED.txt"


def distributable(rel: str) -> bool:
    """Ignore official checksum entries no longer served by PhysioNet HTTP."""
    return not Path(rel).name.endswith("-")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT.parent / "_ecg_soc_physionet")
    parser.add_argument("--database", action="append", choices=[d["abbreviation"] for d in manifest["databases"]])
    args = parser.parse_args()
    selected = set(args.database or [d["abbreviation"] for d in manifest["databases"]])
    expected = {}
    for line in HASHES.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(maxsplit=1)
        abbreviation, version, _ = rel.split("/", 2)
        db = next(item for item in manifest["databases"] if item["abbreviation"] == abbreviation)
        if version != db["version"]:
            raise RuntimeError(f"version mismatch for {abbreviation}")
        if abbreviation in selected and distributable(rel):
            expected[rel] = digest.lower()
    found = {
        path.relative_to(args.data_root).as_posix(): path
        for path in args.data_root.rglob("*") if path.is_file() and not path.name.endswith(".part")
    } if args.data_root.exists() else {}
    missing = sorted(set(expected) - set(found))
    unexpected = sorted(rel for rel in set(found) - set(expected) if rel.split("/", 1)[0] in selected)
    mismatched = sorted(rel for rel in set(expected) & set(found) if sha256(found[rel]) != expected[rel])
    summary = {
        "status": "PASS" if not (missing or unexpected or mismatched) else "FAIL",
        "data_root": str(args.data_root.resolve()), "databases": sorted(selected),
        "excluded_unavailable_historical_checksum_entries": sum(
            1
            for line in HASHES.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
            and line.split(maxsplit=1)[1].strip().split("/", 1)[0] in selected
            and not distributable(line.split(maxsplit=1)[1].strip())
        ),
        "expected_file_count": len(expected), "verified_file_count": len(expected) - len(missing) - len(mismatched),
        "missing": missing, "unexpected": unexpected, "hash_mismatch": mismatched,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
