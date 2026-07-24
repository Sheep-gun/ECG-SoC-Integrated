#!/usr/bin/env python3
"""Rebuild the locked 36-case signed-12-bit digital inputs from PhysioNet.

The historical `.mem` files were local generated artifacts rather than Git
objects.  This script reconstructs them from the fixed PhysioNet downloads,
the retained AFE filter implementation, and the locked board-replay manifest.
Each output is accepted only when its SHA-256 matches the locked manifest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
from collections import defaultdict
from pathlib import Path
import sys

import numpy as np
import scipy
from scipy.signal import lfilter
import wfdb


ROOT = Path(__file__).resolve().parents[2]
AFE_SCRIPTS = ROOT / "design" / "analog" / "xmodel" / "scripts"
sys.path.insert(0, str(AFE_SCRIPTS))

import afe_full  # noqa: E402


CASE_MANIFEST = (
    ROOT
    / "design"
    / "digital"
    / "reports"
    / "final"
    / "board_replay_36_cases.csv"
)
DEFAULT_RAW_ROOT = ROOT.parent / "_ecg_soc_physionet"
DEFAULT_OUTPUT_ROOT = ROOT.parent / "generated_rtl_fpga_test_inputs_36case"
WINDOW_SAMPLES = 1_800_000
SETTLING_SKIP = 2_000
OUTPUT_CHUNK = 500_000
CLASS_DATABASE = {"NSR": "nsrdb", "CHF": "chfdb", "ARR": "mitdb", "AFF": "afdb"}
HEX_LINE_LUT = np.asarray([f"{value:03x}\n".encode("ascii") for value in range(4096)], dtype="S4")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_cases(selected_case: str | None) -> list[dict[str, str]]:
    with CASE_MANIFEST.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if selected_case:
        rows = [row for row in rows if row["case_id"] == selected_case]
        if not rows:
            raise SystemExit(f"Unknown case_id: {selected_case}")
    return rows


def raw_record_path(raw_root: Path, row: dict[str, str]) -> Path:
    database = CLASS_DATABASE[row["class_label"]]
    record_id = row["source_record_id"].split("_")[-1]
    return raw_root / database / "1.0.0" / record_id


def generate_record(
    raw_root: Path,
    output_root: Path,
    rows: list[dict[str, str]],
    overwrite: bool,
) -> list[dict[str, object]]:
    record_path = raw_record_path(raw_root, rows[0])
    header = record_path.with_suffix(".hea")
    if not header.is_file():
        raise FileNotFoundError(f"WFDB record is missing: {header}")

    record = wfdb.rdrecord(str(record_path), physical=False)
    source_rate = float(record.fs)
    source = record.d_signal[:, 0].astype(np.float64)
    output_count = int(len(source) / source_rate * 1000.0)
    source_time = np.arange(len(source), dtype=np.float64) / source_rate

    active: list[dict[str, object]] = []
    for row in rows:
        destination = output_root / row["mem_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not overwrite:
            existing_hash = file_sha256(destination)
            if existing_hash == row["mem_sha256"]:
                active.append({"row": row, "destination": destination, "skip": True})
                continue
            raise RuntimeError(
                f"Existing output has the wrong SHA-256: {destination}. "
                "Use --overwrite only after reviewing it."
            )
        destination.write_bytes(b"")
        active.append({"row": row, "destination": destination, "skip": False})

    pending = [item for item in active if not item["skip"]]
    if pending:
        hp_state = np.zeros(max(len(afe_full._HPF_A), len(afe_full._HPF_B)) - 1, dtype=np.float64)
        notch_state = np.zeros(max(len(afe_full._NOTCH_A), len(afe_full._NOTCH_B)) - 1, dtype=np.float64)
        lpf_state = np.zeros(max(len(afe_full._LPF_A), len(afe_full._LPF_B)) - 1, dtype=np.float64)

        last_required = max(
            SETTLING_SKIP + int(item["row"]["chunk_id"]) * WINDOW_SAMPLES + WINDOW_SAMPLES
            for item in pending
        )
        if last_required > output_count:
            raise RuntimeError(
                f"Record {record_path.name} is too short: required={last_required}, available={output_count}"
            )

        for begin in range(0, last_required, OUTPUT_CHUNK):
            end = min(begin + OUTPUT_CHUNK, last_required)
            target_time = np.arange(begin, end, dtype=np.float64) / 1000.0
            resampled = np.interp(target_time, source_time, source)
            scaled = resampled * afe_full.SCALE
            high_passed, hp_state = lfilter(
                afe_full._HPF_B, afe_full._HPF_A, scaled, zi=hp_state
            )
            gained = high_passed * afe_full.GAIN
            notched, notch_state = lfilter(
                afe_full._NOTCH_B, afe_full._NOTCH_A, gained, zi=notch_state
            )
            low_passed, lpf_state = lfilter(
                afe_full._LPF_B, afe_full._LPF_A, notched, zi=lpf_state
            )
            unsigned = np.clip(
                np.trunc((low_passed + 1.65) / 3.3 * 4095.0), 0, 4095
            ).astype(np.int32)
            signed_hex = ((unsigned - 2048) & 0xFFF).astype(np.int32)

            for item in pending:
                row = item["row"]
                window_begin = SETTLING_SKIP + int(row["chunk_id"]) * WINDOW_SAMPLES
                window_end = window_begin + WINDOW_SAMPLES
                overlap_begin = max(begin, window_begin)
                overlap_end = min(end, window_end)
                if overlap_begin >= overlap_end:
                    continue
                local_begin = overlap_begin - begin
                local_end = overlap_end - begin
                with item["destination"].open("ab") as handle:
                    handle.write(HEX_LINE_LUT[signed_hex[local_begin:local_end]].tobytes())

    results: list[dict[str, object]] = []
    for item in active:
        row = item["row"]
        destination = item["destination"]
        actual_hash = file_sha256(destination)
        sample_count = destination.stat().st_size // 4
        passed = sample_count == WINDOW_SAMPLES and actual_hash == row["mem_sha256"]
        results.append(
            {
                "case_id": row["case_id"],
                "mem_path": row["mem_path"],
                "sample_count": sample_count,
                "expected_sha256": row["mem_sha256"],
                "generated_sha256": actual_hash,
                "status": "PASS" if passed else "FAIL",
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--case-id", help="Generate one locked case for a quick audit")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    raw_root = args.raw_root.resolve()
    output_root = args.output_root.resolve()
    cases = read_cases(args.case_id)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in cases:
        grouped[(row["class_label"], row["source_record_id"])].append(row)

    results: list[dict[str, object]] = []
    for index, rows in enumerate(grouped.values(), start=1):
        print(
            f"GENERATE record={rows[0]['source_record_id']} cases={len(rows)} "
            f"progress={index}/{len(grouped)}",
            flush=True,
        )
        results.extend(generate_record(raw_root, output_root, rows, args.overwrite))
        passed = sum(row["status"] == "PASS" for row in results)
        print(f"LOCKED_INPUT progress={len(results)}/{len(cases)} pass={passed}", flush=True)

    manifest = output_root / "locked_digital_36case_manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(results, key=lambda row: str(row["case_id"])))

    environment = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "wfdb": wfdb.__version__,
        "window_samples": WINDOW_SAMPLES,
        "settling_skip_samples": SETTLING_SKIP,
        "case_manifest_sha256": file_sha256(CASE_MANIFEST),
        "generator_sha256": file_sha256(Path(__file__)),
    }
    (output_root / "locked_digital_36case_environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )

    failures = [row for row in results if row["status"] != "PASS"]
    print(f"LOCKED_INPUT_SUMMARY pass={len(results)-len(failures)}/{len(results)} manifest={manifest}")
    for row in failures:
        print(f"FAIL {row['case_id']} {row['generated_sha256']} != {row['expected_sha256']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
