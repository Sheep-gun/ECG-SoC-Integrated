#!/usr/bin/env python3
"""Run the exact single-thread C++ baseline on all 36 locked cases."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CASES = REPO / "reports" / "final" / "board_replay_36_cases.csv"
DEFAULT_EXE = HERE / "bin" / "cpp_baseline.exe"
DEFAULT_OUT = REPO / "benchmarks" / "accelerator_benefit" / "results" / "cpu_cpp_kernel_runs.csv"
MINGW_BIN = Path(r"C:\Xilinx\Vitis_HLS\2020.2\tps\win64\msys64\mingw64\bin")
CLASSES = ("NSR", "CHF", "ARR", "AFF")
FIELDS = [
    "case_id", "repeat_id", "sample_count", "elapsed_ns", "elapsed_ms",
    "samples_per_second", "final_pred", "final_mem_NSR", "final_mem_CHF",
    "final_mem_ARR", "final_mem_AFF", "output_match", "environment_id",
]


def read_cases() -> list[dict[str, str]]:
    with CASES.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def tokens(line: str) -> dict[str, str]:
    return dict(re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", line))


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--max-cases", type=int)
    args = parser.parse_args()
    if not args.executable.exists():
        raise SystemExit(f"binary missing: {args.executable}; run build_cpp_baseline.py")
    cases = read_cases()
    if args.max_cases is not None:
        cases = cases[: args.max_cases]
    env = os.environ.copy()
    env["PATH"] = str(MINGW_BIN) + os.pathsep + env.get("PATH", "")
    rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        completed = subprocess.run(
            [str(args.executable), str(REPO / case["mem_path"]), str(args.warmups), str(args.repeats)],
            cwd=REPO, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        if completed.returncode:
            raise SystemExit(f"{case['case_id']} failed:\n{completed.stdout}")
        result_lines = [line for line in completed.stdout.splitlines() if line.startswith("CPP_RESULT ")]
        if len(result_lines) != args.repeats:
            raise SystemExit(f"{case['case_id']}: expected {args.repeats} results, got {len(result_lines)}")
        for line in result_lines:
            value = tokens(line)
            pred = int(value["final_pred"])
            memories = {cls: int(value[f"final_mem_{cls}"]) for cls in CLASSES}
            output_match = pred == int(case["expected_final_pred"]) and all(
                memories[cls] == int(case[f"expected_final_mem_{cls}"]) for cls in CLASSES
            )
            if not output_match:
                raise SystemExit(f"{case['case_id']}: exact output mismatch: {line}")
            if value["accepted_samples"] != "1800000" or value["windows"] != "30" or value["decisions"] != "1":
                raise SystemExit(f"{case['case_id']}: profile invariant failed: {line}")
            elapsed = int(value["elapsed_ns"])
            rows.append({
                "case_id": case["case_id"],
                "repeat_id": value["repeat_id"],
                "sample_count": value["sample_count"],
                "elapsed_ns": elapsed,
                "elapsed_ms": f"{elapsed / 1e6:.6f}",
                "samples_per_second": f"{1_800_000 * 1e9 / elapsed:.6f}",
                "final_pred": pred,
                **{f"final_mem_{cls}": memories[cls] for cls in CLASSES},
                "output_match": "true",
                "environment_id": "cpp_verilator_o3_single_thread_windows",
            })
        write_rows(args.output, rows)
        print(json.dumps({"completed": index, "total": len(cases), "case_id": case["case_id"]}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
