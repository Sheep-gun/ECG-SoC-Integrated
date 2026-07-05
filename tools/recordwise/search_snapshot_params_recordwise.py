from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    load_snapshot_module,
    load_strict_split,
    md_table,
    pct,
    strict_rows_from_split,
    write_csv,
    write_json,
    write_log,
)


def evaluate_candidate(snap: Any, rows: list[dict[str, Any]], params: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    evaluated: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        pred = snap.apply_candidate(item, params)
        item["rule_pred"] = int(pred)
        item["rule_pred_label"] = CLASSES[int(pred)]
        evaluated.append(item)
    metrics = {
        split: snap.metric_from_predictions([r for r in evaluated if r["split"] == split], "rule_pred")
        for split in ["train", "val"]
    }
    return metrics, evaluated


def flatten_row(params: dict[str, Any], idx: int, metrics: dict[str, Any]) -> dict[str, Any]:
    train = metrics["train"]
    val = metrics["val"]
    row: dict[str, Any] = {
        "trial": idx,
        "candidate": params.get("candidate", f"candidate_{idx}"),
        "train_accuracy": train["accuracy"],
        "train_macro_f1": train["macro_f1"],
        "train_balanced_accuracy": train["balanced_accuracy"],
        "train_worst_recall": min(float(train["per_class"][cls]["recall"]) for cls in CLASSES),
        "val_accuracy": val["accuracy"],
        "val_macro_f1": val["macro_f1"],
        "val_balanced_accuracy": val["balanced_accuracy"],
        "val_worst_recall": min(float(val["per_class"][cls]["recall"]) for cls in CLASSES),
        "complexity": sum(1 for k, v in params.items() if k != "candidate" and v not in (False, None, 0, "")),
        "params_json": json.dumps(params, sort_keys=True, separators=(",", ":")),
    }
    for split_name, metric in [("train", train), ("val", val)]:
        for cls in CLASSES:
            row[f"{split_name}_{cls}_recall"] = metric["per_class"][cls]["recall"]
            row[f"{split_name}_{cls}_precision"] = metric["per_class"][cls]["precision"]
            row[f"{split_name}_{cls}_f1"] = metric["per_class"][cls]["f1"]
    return row


def sort_key(row: dict[str, Any]) -> tuple[float, float, float, float, float]:
    return (
        float(row["val_macro_f1"]),
        float(row["val_balanced_accuracy"]),
        float(row["val_worst_recall"]),
        float(row["val_accuracy"]),
        -float(row["complexity"]),
    )


def write_summary(top_rows: list[dict[str, Any]], best_params: dict[str, Any], train_metric: dict[str, Any], val_metric: dict[str, Any], trial_count: int) -> Path:
    def support(metric: dict[str, Any], cls: str) -> int:
        if "support" in metric["per_class"][cls]:
            return int(metric["per_class"][cls]["support"])
        if "confusion" in metric:
            return sum(int(v) for v in metric["confusion"][cls].values())
        return 0

    path = REPORTS / "search" / "snapshot_search_summary.md"
    top10 = top_rows[:10]
    lines = [
        "# Strict Record-wise Snapshot Search Summary",
        "",
        f"- Trial count: `{trial_count}`",
        "- Search split scope: `train + validation only`",
        "- test_records_used_for_search: `false`",
        f"- Best validation macro-F1: `{val_metric['macro_f1']:.6f}`",
        f"- Best validation accuracy: `{val_metric['accuracy']:.6f}`",
        "",
        "## Best Validation Per-class Recall",
        "",
        md_table(["class", "recall", "precision", "f1", "support"], [[cls, pct(float(val_metric["per_class"][cls]["recall"])), pct(float(val_metric["per_class"][cls]["precision"])), pct(float(val_metric["per_class"][cls]["f1"])), support(val_metric, cls)] for cls in CLASSES]),
        "",
        "## Selected Params",
        "",
        "```json",
        json.dumps(best_params, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Top 10 Candidates",
        "",
        md_table(
            ["rank", "candidate", "val_macro_f1", "val_accuracy", "val_worst_recall", "complexity"],
            [
                [idx + 1, row["candidate"], f"{float(row['val_macro_f1']):.6f}", f"{float(row['val_accuracy']):.6f}", f"{float(row['val_worst_recall']):.6f}", row["complexity"]]
                for idx, row in enumerate(top10)
            ],
        ),
        "",
        "## Train/Validation Confusion Matrices",
        "",
        "Train:",
        "",
        md_table(["true", *CLASSES], [[cls, *train_metric["confusion"][cls].values()] for cls in CLASSES]),
        "",
        "Validation:",
        "",
        md_table(["true", *CLASSES], [[cls, *val_metric["confusion"][cls].values()] for cls in CLASSES]),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Search snapshot C24 rule candidates on strict record-wise train/val only.")
    parser.add_argument("--resume", action="store_true", help="Accepted for workflow compatibility; current candidate set is deterministic.")
    parser.add_argument("--max-trials", type=int, default=0, help="0 means evaluate all snapshot candidates.")
    args = parser.parse_args()

    snap = load_snapshot_module()
    split_rows = load_strict_split()
    strict_rows = strict_rows_from_split(split_rows)
    search_rows = [r for r in strict_rows if r["split"] in ("train", "val")]
    if any(r["split"] == "test" for r in search_rows):
        raise RuntimeError("test row leaked into snapshot search rows")

    candidates = snap.candidate_grid()
    if args.max_trials and args.max_trials > 0:
        candidates = candidates[: args.max_trials]

    trial_path = REPORTS / "search" / "snapshot_trials.jsonl"
    trial_path.parent.mkdir(parents=True, exist_ok=True)
    trial_rows: list[dict[str, Any]] = []
    best: tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]] | None = None
    with trial_path.open("w", encoding="utf-8") as f:
        for idx, params in enumerate(candidates, 1):
            metrics, evaluated = evaluate_candidate(snap, search_rows, params)
            row = flatten_row(params, idx, metrics)
            trial_rows.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if best is None or sort_key(row) > sort_key(flatten_row(best[0], -1, best[1])):
                best = (dict(params), metrics, evaluated)
            if idx % 100 == 0:
                print(f"snapshot trials {idx}/{len(candidates)}", flush=True)

    trial_rows.sort(key=sort_key, reverse=True)
    top_path = REPORTS / "search" / "snapshot_top_candidates.csv"
    write_csv(top_path, trial_rows[: min(100, len(trial_rows))])
    if best is None:
        raise RuntimeError("no snapshot candidate evaluated")
    best_params, best_metrics, _ = best
    best_payload = {
        "selected_from": "strict record-wise train/validation snapshot search",
        "test_used_for_selection": False,
        "trial_count": len(candidates),
        "params": best_params,
        "train_metrics": best_metrics["train"],
        "val_metrics": best_metrics["val"],
    }
    best_path = CONFIGS / "best_snapshot_params.json"
    write_json(best_path, best_payload)
    summary_path = write_summary(trial_rows, best_params, best_metrics["train"], best_metrics["val"], len(candidates))
    write_log("search_snapshot_params_recordwise", sys.argv, [trial_path, top_path, best_path, summary_path], {"test_records_used_for_search": False, "trial_count": len(candidates)})
    print(summary_path)


if __name__ == "__main__":
    main()
