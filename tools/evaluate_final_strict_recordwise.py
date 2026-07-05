#!/usr/bin/env python3
"""Recheck the final strict record-wise metrics from committed CSV artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FINAL = REPO / "reports" / "final"
CHUNK_CSV = FINAL / "strict_recordwise" / "structural_final_test_predictions.csv"
RECORD_CSV = FINAL / "strict_recordwise" / "structural_final_test_record_predictions.csv"
METRICS_JSON = FINAL / "final_metrics.json"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def accuracy(rows: list[dict[str, str]]) -> tuple[int, int, float]:
    total = len(rows)
    correct = sum(1 for row in rows if row.get("correct") == "1")
    return correct, total, round(correct * 100.0 / total, 2) if total else 0.0


def main() -> int:
    metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    chunk_correct, chunk_total, chunk_acc = accuracy(read_rows(CHUNK_CSV))
    record_correct, record_total, record_acc = accuracy(read_rows(RECORD_CSV))

    expected = {
        "final_model_id": "structural_guarded_silent_aff_1008710",
        "final_test_chunk": {"correct": chunk_correct, "total": chunk_total, "accuracy_percent": chunk_acc},
        "final_test_record_majority": {
            "correct": record_correct,
            "total": record_total,
            "accuracy_percent": record_acc,
        },
    }

    failures: list[str] = []
    if metrics.get("final_model_id") != expected["final_model_id"]:
        failures.append(f"final_model_id mismatch: {metrics.get('final_model_id')}")
    for section in ["final_test_chunk", "final_test_record_majority"]:
        for key, value in expected[section].items():
            if metrics.get(section, {}).get(key) != value:
                failures.append(f"{section}.{key}: expected {value}, got {metrics.get(section, {}).get(key)}")

    print(json.dumps(expected, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit("\n".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
