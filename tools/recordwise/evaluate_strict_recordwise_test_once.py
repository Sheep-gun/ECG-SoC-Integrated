from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    confusion_rows,
    load_final_module,
    load_snapshot_module,
    load_strict_split,
    metric_from_pairs,
    md_table,
    pct,
    read_json,
    record_lists_from_split,
    split_json_path,
    strict_rows_from_split,
    write_csv,
    write_json,
    write_log,
)


def argmax(values: list[int]) -> int:
    best = 0
    for idx in range(1, len(values)):
        if values[idx] > values[best]:
            best = idx
    return best


def rows_with_snapshot(rows: list[dict[str, Any]], params: dict[str, Any]) -> list[dict[str, Any]]:
    snap = load_snapshot_module()
    out = []
    for row in rows:
        item = dict(row)
        pred = snap.apply_candidate(item, params)
        item["snapshot_pred_class"] = int(pred)
        item["snapshot_pred_label"] = CLASSES[int(pred)]
        out.append(item)
    return out


def build_test_chunks(final_mod: Any, rows: list[dict[str, Any]]) -> list[Any]:
    return final_mod.build_chunks([r for r in rows if r["split"] == "test"])


def prediction_rows(chunks: list[Any], pred: dict[str, int], details: dict[str, dict[str, Any]], source_by_case: dict[str, str]) -> list[dict[str, Any]]:
    rows = []
    for chunk in chunks:
        row: dict[str, Any] = {
            "case_id": chunk.case_id,
            "source_record_id": source_by_case[chunk.case_id],
            "class_label": chunk.class_label,
            "class_id": chunk.class_id,
            "record_id": chunk.record_id,
            "chunk_id": chunk.chunk_id,
            "chunk_file": chunk.chunk_file,
            "pred_class": pred[chunk.case_id],
            "pred_label": CLASSES[pred[chunk.case_id]],
            "correct": int(pred[chunk.case_id] == chunk.class_id),
        }
        row.update(details[chunk.case_id])
        rows.append(row)
    return rows


def record_level(rows: list[dict[str, Any]], method: str) -> tuple[list[int], list[int], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_record_id"]].append(row)
    true_ids: list[int] = []
    pred_ids: list[int] = []
    out_rows: list[dict[str, Any]] = []
    for record, items in sorted(grouped.items()):
        cls_id = int(items[0]["class_id"])
        if method == "majority":
            counts = [0, 0, 0, 0]
            for item in items:
                counts[int(item["pred_class"])] += 1
            pred = argmax(counts)
            evidence = counts
        elif method == "final_mem_sum":
            sums = [0, 0, 0, 0]
            for item in items:
                for idx, cls in enumerate(CLASSES):
                    sums[idx] += int(item[f"final_mem_{cls}"])
            pred = argmax(sums)
            evidence = sums
        else:
            raise ValueError(method)
        true_ids.append(cls_id)
        pred_ids.append(pred)
        out_rows.append(
            {
                "source_record_id": record,
                "class_label": CLASSES[cls_id],
                "method": method,
                "pred_class": pred,
                "pred_label": CLASSES[pred],
                "correct": int(pred == cls_id),
                "chunk_count": len(items),
                "evidence_NSR": evidence[0],
                "evidence_CHF": evidence[1],
                "evidence_ARR": evidence[2],
                "evidence_AFF": evidence[3],
            }
        )
    return true_ids, pred_ids, out_rows


def write_summary(metrics: dict[str, Any], eval_count: int, warning: str | None) -> Any:
    path = REPORTS / "final_test" / "strict_recordwise_test_summary.md"
    chunk = metrics["chunk_level"]
    rec_majority = metrics["record_level_majority"]
    lines = [
        "# Strict Record-wise Final Test Summary",
        "",
        f"- Evaluation timestamp: `{metrics['timestamp_utc']}`",
        f"- test_evaluation_count: `{eval_count}`",
        f"- Warning: `{warning or 'none'}`",
        "- Params source: `configs/recordwise/best_strict_recordwise_params_locked.json`",
        "- Selection after test: `false`",
        "",
        "## Chunk-level Metrics",
        "",
        md_table(
            ["metric", "value"],
            [
                ["accuracy", pct(chunk["accuracy"])],
                ["macro-F1", pct(chunk["macro_f1"])],
                ["balanced accuracy", pct(chunk["balanced_accuracy"])],
                ["total chunks", chunk["total"]],
                ["correct chunks", chunk["correct"]],
            ],
        ),
        "",
        "## Record-level Metrics",
        "",
        md_table(
            ["method", "accuracy", "macro-F1", "balanced accuracy", "records"],
            [
                ["majority", pct(rec_majority["accuracy"]), pct(rec_majority["macro_f1"]), pct(rec_majority["balanced_accuracy"]), rec_majority["total"]],
                ["final_mem_sum", pct(metrics["record_level_final_mem_sum"]["accuracy"]), pct(metrics["record_level_final_mem_sum"]["macro_f1"]), pct(metrics["record_level_final_mem_sum"]["balanced_accuracy"]), metrics["record_level_final_mem_sum"]["total"]],
            ],
        ),
        "",
        "## Per-class Chunk Recall",
        "",
        md_table(["class", "recall", "precision", "f1", "support"], [[cls, pct(float(chunk["per_class"][cls]["recall"])), pct(float(chunk["per_class"][cls]["precision"])), pct(float(chunk["per_class"][cls]["f1"])), chunk["per_class"][cls]["support"]] for cls in CLASSES]),
        "",
        "## Interpretation Boundary",
        "",
        "이 결과는 source_record_id 기준 strict split에서 train/validation-only search 이후 locked params로 수행한 held-out test 1회 평가이다. 기존 chunk-level 32/36 = 88.89% 결과와 protocol이 다르므로 같은 의미로 직접 비교하지 않는다.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate locked strict record-wise params on held-out test records.")
    parser.add_argument("--allow-rerun", action="store_true")
    args = parser.parse_args()

    final_dir = REPORTS / "final_test"
    count_path = final_dir / "test_evaluation_count.json"
    warning = None
    split_payload = read_json(split_json_path())
    split_hash = split_payload.get("split_hash")
    if count_path.exists():
        count_payload = read_json(count_path)
        if count_payload.get("split_hash") == split_hash:
            prev = int(count_payload.get("test_evaluation_count", 0))
        else:
            prev = 0
        if prev and not args.allow_rerun:
            warning = f"test was already evaluated {prev} time(s); rerun recorded for reproducibility only"
    else:
        prev = 0
    eval_count = prev + 1

    locked_path = CONFIGS / "best_strict_recordwise_params_locked.json"
    locked = read_json(locked_path)
    snapshot_params = locked["selected_snapshot_params"]["params"]
    final_params = locked["selected_final_membrane_params"]["params"]
    split_rows = load_strict_split()
    strict_rows = rows_with_snapshot(strict_rows_from_split(split_rows), snapshot_params)
    final_mod = load_final_module()
    test_chunks = build_test_chunks(final_mod, strict_rows)
    source_by_case = {}
    for row in strict_rows:
        if row["split"] == "test":
            source_by_case[str(row["case_id"])] = row["source_record_id"]

    pred, details = final_mod.apply_candidate(test_chunks, final_params)
    chunk_true = [chunk.class_id for chunk in test_chunks]
    chunk_pred = [pred[chunk.case_id] for chunk in test_chunks]
    chunk_metric = metric_from_pairs(chunk_true, chunk_pred)
    pred_rows = prediction_rows(test_chunks, pred, details, source_by_case)
    maj_true, maj_pred, maj_rows = record_level(pred_rows, "majority")
    mem_true, mem_pred, mem_rows = record_level(pred_rows, "final_mem_sum")
    maj_metric = metric_from_pairs(maj_true, maj_pred)
    mem_metric = metric_from_pairs(mem_true, mem_pred)

    record_lists = record_lists_from_split(split_rows)
    test_record_count_by_class = {
        cls: len({row["source_record_id"] for row in split_rows if row["split"] == "test" and row["class_label"] == cls})
        for cls in CLASSES
    }
    metrics = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_evaluation_count": eval_count,
        "warning": warning,
        "split_hash": split_hash,
        "test_used_for_selection": False,
        "locked_params_path": str(locked_path),
        "test_records": record_lists["test"],
        "test_record_count_by_class": test_record_count_by_class,
        "test_chunk_count_by_class": dict(Counter(row["class_label"] for row in pred_rows)),
        "chunk_level": chunk_metric,
        "record_level_majority": maj_metric,
        "record_level_final_mem_sum": mem_metric,
    }
    pred_path = final_dir / "strict_recordwise_test_predictions.csv"
    confusion_path = final_dir / "strict_recordwise_test_confusion_matrix.csv"
    metrics_path = final_dir / "strict_recordwise_test_metrics.json"
    record_pred_path = final_dir / "strict_recordwise_test_record_predictions.csv"
    write_csv(pred_path, pred_rows)
    write_csv(confusion_path, confusion_rows(chunk_metric))
    write_csv(record_pred_path, maj_rows + mem_rows)
    write_json(metrics_path, metrics)
    write_json(count_path, {"test_evaluation_count": eval_count, "split_hash": split_hash, "last_timestamp_utc": metrics["timestamp_utc"], "warning": warning})
    summary_path = write_summary(metrics, eval_count, warning)
    write_log("evaluate_strict_recordwise_test_once", sys.argv, [pred_path, confusion_path, metrics_path, record_pred_path, summary_path, count_path], {"test_evaluation_count": eval_count, "warning": warning})
    print(summary_path)


if __name__ == "__main__":
    main()
