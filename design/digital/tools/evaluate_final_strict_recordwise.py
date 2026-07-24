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
SUMMARY_JSON = FINAL / "strict_recordwise" / "strict_recordwise_metric_summary.json"
CHUNK_CLASS_CSV = FINAL / "strict_recordwise" / "final_test_chunk_class_metrics.csv"
RECORD_CLASS_CSV = FINAL / "strict_recordwise" / "final_test_record_majority_class_metrics.csv"
CLASS_LABELS = ["NSR", "CHF", "ARR", "AFF"]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def accuracy(rows: list[dict[str, str]]) -> tuple[int, int, float]:
    total = len(rows)
    correct = sum(1 for row in rows if row.get("correct") == "1")
    return correct, total, round(correct * 100.0 / total, 2) if total else 0.0


def pct(value: float) -> float:
    return round(value * 100.0, 2)


def per_class_metrics(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for class_id, label in enumerate(CLASS_LABELS):
        support = sum(1 for row in rows if int(row["class_id"]) == class_id) if "class_id" in rows[0] else sum(
            1 for row in rows if row["class_label"] == label
        )
        predicted = sum(1 for row in rows if int(row["pred_class"]) == class_id)
        tp = sum(1 for row in rows if row["class_label"] == label and int(row["pred_class"]) == class_id)
        fp = predicted - tp
        fn = support - tp
        precision = tp / predicted if predicted else 0.0
        recall = tp / support if support else 0.0
        f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
        out.append(
            {
                "class_label": label,
                "support": support,
                "predicted": predicted,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision_percent": pct(precision),
                "recall_percent": pct(recall),
                "f1_percent": pct(f1),
            }
        )
    return out


def summary_from_rows(rows: list[dict[str, str]]) -> dict[str, object]:
    correct, total, acc = accuracy(rows)
    class_metrics = per_class_metrics(rows)
    macro_f1 = round(sum(float(row["f1_percent"]) for row in class_metrics) / len(class_metrics), 2)
    balanced = round(sum(float(row["recall_percent"]) for row in class_metrics) / len(class_metrics), 2)
    return {
        "correct": correct,
        "total": total,
        "accuracy_percent": acc,
        "macro_f1_percent": macro_f1,
        "balanced_accuracy_percent": balanced,
        "class_metrics": class_metrics,
    }


def write_class_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fields = [
        "class_label",
        "support",
        "predicted",
        "tp",
        "fp",
        "fn",
        "precision_percent",
        "recall_percent",
        "f1_percent",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def compact_metrics(summary: dict[str, object]) -> dict[str, object]:
    return {
        "correct": summary["correct"],
        "total": summary["total"],
        "accuracy_percent": summary["accuracy_percent"],
        "macro_f1_percent": summary["macro_f1_percent"],
        "balanced_accuracy_percent": summary["balanced_accuracy_percent"],
        "class_recall_percent": {
            str(row["class_label"]): row["recall_percent"] for row in summary["class_metrics"]  # type: ignore[index]
        },
    }


def main() -> int:
    metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    chunk_summary = summary_from_rows(read_rows(CHUNK_CSV))
    record_summary = summary_from_rows(read_rows(RECORD_CSV))

    expected = {
        "final_model_id": "structural_guarded_silent_aff_1008710",
        "final_test_chunk": compact_metrics(chunk_summary),
        "final_test_record_majority": compact_metrics(record_summary),
    }

    write_class_csv(CHUNK_CLASS_CSV, chunk_summary["class_metrics"])  # type: ignore[arg-type]
    write_class_csv(RECORD_CLASS_CSV, record_summary["class_metrics"])  # type: ignore[arg-type]
    SUMMARY_JSON.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    failures: list[str] = []
    if metrics.get("final_model_id") != expected["final_model_id"]:
        failures.append(f"final_model_id mismatch: {metrics.get('final_model_id')}")
    for section in ["final_test_chunk", "final_test_record_majority"]:
        for key, value in expected[section].items():
            if key == "class_recall_percent":
                continue
            if metrics.get(section, {}).get(key) != value:
                failures.append(f"{section}.{key}: expected {value}, got {metrics.get(section, {}).get(key)}")

    print(json.dumps(expected, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit("\n".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
