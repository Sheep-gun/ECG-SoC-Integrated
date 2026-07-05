from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    load_final_module,
    load_snapshot_module,
    load_strict_split,
    metric_from_pairs,
    pct,
    read_json,
    stable_bucket,
    strict_rows_from_split,
    write_csv,
    write_log,
)


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


def evaluate_rows(rows: list[dict[str, Any]], final_params: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    final_mod = load_final_module()
    chunks = final_mod.build_chunks(rows)
    pred, details = final_mod.apply_candidate(chunks, final_params)
    metric = final_mod.metric_for_predictions(chunks, pred)
    out = []
    source_by_case = {str(row["case_id"]): row["source_record_id"] for row in rows}
    for chunk in chunks:
        item = {
            "case_id": chunk.case_id,
            "source_record_id": source_by_case[str(chunk.case_id)],
            "class_label": chunk.class_label,
            "class_id": chunk.class_id,
            "pred_class": pred[chunk.case_id],
            "pred_label": CLASSES[pred[chunk.case_id]],
            "correct": int(pred[chunk.case_id] == chunk.class_id),
            "chunk_file": chunk.chunk_file,
        }
        item.update(details[chunk.case_id])
        out.append(item)
    return metric, out


def main() -> None:
    parser = argparse.ArgumentParser(description="Run locked-parameter group-wise robustness audit.")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    locked = read_json(CONFIGS / "best_strict_recordwise_params_locked.json")
    snapshot_params = locked["selected_snapshot_params"]["params"]
    final_params = locked["selected_final_membrane_params"]["params"]
    split_rows = load_strict_split()
    rows = rows_with_snapshot(strict_rows_from_split(split_rows), snapshot_params)
    records = sorted({row["source_record_id"] for row in rows})
    fold_for_record = {record: stable_bucket(record, args.seed) % args.folds for record in records}
    fold_rows = []
    prediction_rows = []
    for fold in range(args.folds):
        fold_eval_rows = [row for row in rows if fold_for_record[row["source_record_id"]] == fold]
        metric, preds = evaluate_rows(fold_eval_rows, final_params)
        fold_rows.append(
            {
                "fold": fold,
                "records": len({row["source_record_id"] for row in fold_eval_rows}),
                "chunks": metric["total"],
                "accuracy": metric["accuracy"],
                "macro_f1": metric["macro_f1"],
                "balanced_accuracy": metric["balanced_accuracy"],
                "min_recall": metric["min_recall"],
            }
        )
        for pred in preds:
            pred["fold"] = fold
            prediction_rows.append(pred)

    loro_rows = []
    by_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_record[row["source_record_id"]].append(row)
    for record, rec_rows in sorted(by_record.items()):
        metric, preds = evaluate_rows(rec_rows, final_params)
        counts = [0, 0, 0, 0]
        true_ids = []
        pred_ids = []
        for pred in preds:
            counts[int(pred["pred_class"])] += 1
            true_ids.append(int(pred["class_id"]))
            pred_ids.append(int(pred["pred_class"]))
        rec_metric = metric_from_pairs(true_ids, pred_ids)
        loro_rows.append(
            {
                "source_record_id": record,
                "class_label": rec_rows[0]["class_label"],
                "chunks": rec_metric["total"],
                "accuracy": rec_metric["accuracy"],
                "pred_NSR": counts[0],
                "pred_CHF": counts[1],
                "pred_ARR": counts[2],
                "pred_AFF": counts[3],
            }
        )

    cv_dir = REPORTS / "cv"
    fold_csv = cv_dir / "groupkfold_predictions.csv"
    fold_summary_csv = cv_dir / "groupkfold_summary.csv"
    loro_csv = cv_dir / "loro_locked_params_by_record.csv"
    write_csv(fold_csv, prediction_rows)
    write_csv(fold_summary_csv, fold_rows)
    write_csv(loro_csv, loro_rows)
    md = cv_dir / "groupkfold_summary.md"
    avg_acc = sum(float(row["accuracy"]) for row in fold_rows) / len(fold_rows)
    avg_f1 = sum(float(row["macro_f1"]) for row in fold_rows) / len(fold_rows)
    lines = [
        "# Strict Record-wise GroupKFold Robustness Audit",
        "",
        "This is a locked-parameter audit, not a second final test and not a parameter-selection loop.",
        "",
        f"- Folds: `{args.folds}`",
        f"- Mean fold accuracy: `{pct(avg_acc)}`",
        f"- Mean fold macro-F1: `{pct(avg_f1)}`",
        "",
        "| fold | records | chunks | accuracy | macro-F1 | balanced accuracy |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in fold_rows:
        lines.append(
            f"| {row['fold']} | {row['records']} | {row['chunks']} | {pct(float(row['accuracy']))} | {pct(float(row['macro_f1']))} | {pct(float(row['balanced_accuracy']))} |"
        )
    md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    loro_md = cv_dir / "loro_summary.md"
    by_class = defaultdict(list)
    for row in loro_rows:
        by_class[row["class_label"]].append(row)
    lines = [
        "# Strict Record-wise LORO-style Locked-Parameter Audit",
        "",
        "Each row holds out one source record for reporting only. Parameters are already locked and are not retrained per record.",
        "",
        "| class | records | chunks | mean record accuracy |",
        "|---|---:|---:|---:|",
    ]
    for cls in CLASSES:
        items = by_class[cls]
        chunks = sum(int(item["chunks"]) for item in items)
        acc = sum(float(item["accuracy"]) for item in items) / len(items) if items else 0.0
        lines.append(f"| {cls} | {len(items)} | {chunks} | {pct(acc)} |")
    loro_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    write_log("run_groupkfold_recordwise_cv", sys.argv, [fold_csv, fold_summary_csv, loro_csv, md, loro_md], {"locked_params_only": True})
    print(md)
    print(loro_md)


if __name__ == "__main__":
    main()
