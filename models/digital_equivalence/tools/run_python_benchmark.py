#!/usr/bin/env python3
"""Run resumable single-process Python kernel and end-to-end measurements."""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any


for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np

from locked_integer_inference import infer_loaded
from snapshot_c24_rtl_exact import s12_from_hex_mem


INTEGRATED_ROOT = Path(__file__).resolve().parents[3]
DIGITAL_ROOT = INTEGRATED_ROOT / "design" / "digital"
BENCH = INTEGRATED_ROOT / "models" / "digital_equivalence"
CASES = DIGITAL_ROOT / "reports" / "final" / "board_replay_36_cases.csv"
KERNEL_OUT = BENCH / "results/cpu_python_kernel_runs.csv"
E2E_OUT = BENCH / "results/cpu_python_end_to_end_runs.csv"
ENV_OUT = BENCH / "results/cpu_environment.json"
CLASSES = ("NSR", "CHF", "ARR", "AFF")
FIELDS = ["case_id", "repeat_id", "sample_count", "elapsed_ns", "elapsed_ms", "samples_per_second", "final_pred", *[f"final_mem_{cls}" for cls in CLASSES], "output_match", "environment_id"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def exact(result: dict[str, Any], case: dict[str, str]) -> bool:
    return result["final_pred"] == int(case["expected_final_pred"]) and all(
        result[f"final_mem_{cls}"] == int(case[f"expected_final_mem_{cls}"]) for cls in CLASSES
    )


def row(case_id: str, repeat_id: int, elapsed: int, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case_id, "repeat_id": repeat_id, "sample_count": result["sample_count"],
        "elapsed_ns": elapsed, "elapsed_ms": f"{elapsed / 1e6:.6f}",
        "samples_per_second": f"{1_800_000 * 1e9 / elapsed:.6f}", "final_pred": result["final_pred"],
        **{f"final_mem_{cls}": result[f"final_mem_{cls}"] for cls in CLASSES},
        "output_match": "true", "environment_id": "python_exact_single_process_windows",
    }


def environment(status: str, warmups: int, repeats: int) -> dict[str, Any]:
    try:
        cpu_model = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
            text=True, timeout=15,
        ).strip()
    except Exception:
        cpu_model = platform.processor() or "UNKNOWN"
    return {
        "environment_id": "python_exact_single_process_windows", "status": status,
        "cpu_model": cpu_model, "os": platform.platform(),
        "python_version": platform.python_version(), "python_executable": os.sys.executable,
        "numpy_version": np.__version__, "processes": 1, "warmups_per_case": warmups,
        "measured_repetitions_per_case": repeats, "timer": "time.perf_counter_ns",
        "canonical_sample_gap_cycles": 2, "post_done_ticks": 37,
        "thread_environment": {name: os.environ[name] for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS")},
        "kernel_scope": "samples already loaded in RAM through final result",
        "end_to_end_scope": "input file open/read/parse through final result",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-cases", type=int)
    args = parser.parse_args()
    cases = read_csv(CASES)
    if args.max_cases is not None:
        cases = cases[:args.max_cases]
    kernel_rows = read_csv(KERNEL_OUT) if args.resume else []
    e2e_rows = read_csv(E2E_OUT) if args.resume else []
    ENV_OUT.write_text(json.dumps(environment("RUNNING", args.warmups, args.repeats), indent=2) + "\n", encoding="utf-8")

    for index, case in enumerate(cases, start=1):
        done = {int(item["repeat_id"]) for item in kernel_rows if item["case_id"] == case["case_id"]}
        if done == set(range(args.repeats)):
            print(f"PY_BENCH skipped={index} total={len(cases)} case_id={case['case_id']}", flush=True)
            continue
        path = DIGITAL_ROOT / case["mem_path"]
        loaded = s12_from_hex_mem(path)
        for _ in range(args.warmups):
            warm = infer_loaded(loaded, inter_sample_idle_cycles=2, post_done_ticks=37)
            if not exact(warm, case):
                raise SystemExit(f"warmup equivalence failed: {case['case_id']}")
        for repeat_id in range(args.repeats):
            if repeat_id in done:
                continue
            e2e_begin = time.perf_counter_ns()
            parsed = s12_from_hex_mem(path)
            kernel_begin = time.perf_counter_ns()
            result = infer_loaded(parsed, inter_sample_idle_cycles=2, post_done_ticks=37)
            kernel_end = time.perf_counter_ns()
            e2e_end = time.perf_counter_ns()
            if not exact(result, case):
                raise SystemExit(f"measured equivalence failed: {case['case_id']} repeat {repeat_id}")
            kernel_rows.append(row(case["case_id"], repeat_id, kernel_end - kernel_begin, result))
            e2e_rows.append(row(case["case_id"], repeat_id, e2e_end - e2e_begin, result))
            write_csv(KERNEL_OUT, kernel_rows)
            write_csv(E2E_OUT, e2e_rows)
            print(f"PY_BENCH case={index}/{len(cases)} case_id={case['case_id']} repeat={repeat_id + 1}/{args.repeats}", flush=True)

    expected = len(cases) * args.repeats
    status = "COMPLETED" if len(kernel_rows) == expected and len(e2e_rows) == expected else "PARTIAL"
    ENV_OUT.write_text(json.dumps(environment(status, args.warmups, args.repeats), indent=2) + "\n", encoding="utf-8")
    return 0 if status == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
