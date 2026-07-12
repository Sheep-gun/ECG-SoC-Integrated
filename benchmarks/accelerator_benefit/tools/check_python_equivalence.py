#!/usr/bin/env python3
"""Run the untimed 36-case Python/RTL equivalence gate in parallel."""

from __future__ import annotations

import argparse
import csv
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
CASES = REPO / "reports/final/board_replay_36_cases.csv"
OUT = REPO / "benchmarks/accelerator_benefit/results/python_equivalence_gate.csv"
CLASSES = ("NSR", "CHF", "ARR", "AFF")


def read_cases() -> list[dict[str, str]]:
    with CASES.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def run_case(case: dict[str, str]) -> dict[str, Any]:
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    from locked_integer_inference import infer_file

    result = infer_file(REPO / case["mem_path"], inter_sample_idle_cycles=2, post_done_ticks=37)
    pred_match = result["final_pred"] == int(case["expected_final_pred"])
    mem_match = all(result[f"final_mem_{cls}"] == int(case[f"expected_final_mem_{cls}"]) for cls in CLASSES)
    return {
        "case_id": case["case_id"], "sample_count": result["sample_count"],
        "snapshot_count": result["snapshot_count"], "final_pred": result["final_pred"],
        **{f"final_mem_{cls}": result[f"final_mem_{cls}"] for cls in CLASSES},
        "pred_match": str(pred_match).lower(), "mem_match": str(mem_match).lower(),
    }


def write_rows(rows: list[dict[str, Any]]) -> None:
    fields = ["case_id", "sample_count", "snapshot_count", "final_pred", *[f"final_mem_{cls}" for cls in CLASSES], "pred_match", "mem_match"]
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: row["case_id"]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    rows: list[dict[str, Any]] = []
    cases = read_cases()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(run_case, case): case["case_id"] for case in cases}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            write_rows(rows)
            print(f"PY_EQUIV completed={len(rows)} total={len(cases)} case_id={row['case_id']} pred_match={row['pred_match']} mem_match={row['mem_match']}", flush=True)
            if row["pred_match"] != "true" or row["mem_match"] != "true":
                raise SystemExit(f"Python equivalence failed: {row['case_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
