#!/usr/bin/env python3
"""Resume and verify fixed-version PhysioNet downloads outside the Git tree."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets" / "dataset_manifest.yaml"
HASHES = ROOT / "datasets" / "SHA256SUMS_EXPECTED.txt"


def distributable(rel: str) -> bool:
    """Return whether PhysioNet still exposes this checksum entry over HTTP.

    Several official SHA256SUMS files retain historical editor-backup names
    such as ``*.hea-`` and ``*.atr-`` that the fixed-version HTTP directory no
    longer serves.  They are not waveform inputs and cannot be downloaded.
    """
    return not Path(rel).name.endswith("-")


def expected() -> dict[str, str]:
    result = {}
    for line in HASHES.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        digest, rel = line.split(maxsplit=1)
        result[rel.strip().replace("\\", "/")] = digest.lower()
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path, digest: str, fallback_url: str | None = None) -> str:
    if destination.exists() and sha256(destination) == digest:
        return "already_verified"
    part = destination.with_suffix(destination.suffix + ".part")
    destination.parent.mkdir(parents=True, exist_ok=True)
    offset = part.stat().st_size if part.exists() else 0
    request = urllib.request.Request(url, headers={"User-Agent": "ECG-SoC-Integrated dataset fetch/1"})
    if offset:
        request.add_header("Range", f"bytes={offset}-")
    try:
        response = urllib.request.urlopen(request, timeout=120)
    except urllib.error.HTTPError as exc:
        if exc.code == 416 and part.exists():
            response = None
        else:
            raise
    if response is not None:
        append = offset > 0 and getattr(response, "status", None) == 206
        if offset and not append:
            offset = 0
        with response, part.open("ab" if append else "wb") as handle:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                handle.write(block)
    if not part.exists() or sha256(part) != digest:
        # The public S3 mirror occasionally serves an object whose bytes lag
        # the fixed-version website checksum.  Retry that one object from the
        # authoritative PhysioNet version URL instead of accepting it.
        if fallback_url and fallback_url != url:
            part.unlink(missing_ok=True)
            destination.unlink(missing_ok=True)
            return download(fallback_url, destination, digest)
        raise RuntimeError(f"SHA256 mismatch: {url}")
    part.replace(destination)
    return "downloaded_verified"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=ROOT.parent / "_ecg_soc_physionet")
    parser.add_argument("--database", action="append", choices=[d["abbreviation"] for d in manifest["databases"]])
    parser.add_argument("--jobs", type=int, default=8, help="parallel file downloads")
    parser.add_argument(
        "--source",
        choices=("s3", "physionet"),
        default="s3",
        help="official PhysioNet public S3 mirror (default) or website",
    )
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    selected = set(args.database or [d["abbreviation"] for d in manifest["databases"]])
    hashes = expected()
    summary = {
        "status": "PASS",
        "data_root": str(args.data_root.resolve()),
        "files": {},
        "unavailable_historical_checksum_entries": [],
    }
    jobs = []
    for rel, digest in hashes.items():
        abbreviation, version, remainder = rel.split("/", 2)
        if abbreviation not in selected:
            continue
        if not distributable(rel):
            summary["unavailable_historical_checksum_entries"].append(rel)
            continue
        db = next(item for item in manifest["databases"] if item["abbreviation"] == abbreviation)
        if version != db["version"]:
            raise RuntimeError(f"manifest/hash version mismatch for {abbreviation}: {version}")
        fallback_url = None
        if args.source == "s3":
            url = f"https://physionet-open.s3.amazonaws.com/{abbreviation}/{version}/{remainder}"
            fallback_url = db["download_base_url"] + remainder
        else:
            url = db["download_base_url"] + remainder
        jobs.append((rel, url, args.data_root / rel, digest, fallback_url))
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(download, url, destination, digest, fallback_url): rel
            for rel, url, destination, digest, fallback_url in jobs
        }
        for future in as_completed(futures):
            rel = futures[future]
            state = future.result()
            summary["files"][rel] = state
            print(f"{state}: {rel}", file=sys.stderr, flush=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
