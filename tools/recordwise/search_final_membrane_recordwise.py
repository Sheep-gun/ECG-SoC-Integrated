from __future__ import annotations

import argparse
import json
import sys
from itertools import islice
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    SPLITS,
    load_final_module,
    load_snapshot_module,
    load_strict_split,
    md_table,
    pct,
    read_json,
    record_lists_from_split,
    sha256_json,
    split_json_path,
    strict_rows_from_split,
    write_csv,
    write_json,
    write_log,
)


def rows_with_snapshot_params(rows: list[dict[str, Any]], snapshot_params: dict[str, Any]) -> list[dict[str, Any]]:
    snap = load_snapshot_module()
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        pred = snap.apply_candidate(item, snapshot_params)
        item["snapshot_pred_class"] = int(pred)
        item["snapshot_pred_label"] = CLASSES[int(pred)]
        out.append(item)
    return out


def chunks_by_split(final_mod: Any, rows: list[dict[str, Any]]) -> dict[str, list[Any]]:
    out: dict[str, list[Any]] = {}
    for split in SPLITS:
        out[split] = final_mod.build_chunks([r for r in rows if r["split"] == split])
    return out


def evaluate(final_mod: Any, chunks: list[Any], params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int], dict[str, dict[str, Any]]]:
    pred, details = final_mod.apply_candidate(chunks, params)
    metric = final_mod.metric_for_predictions(chunks, pred)
    return metric, pred, details


def flatten(params: dict[str, Any], idx: int, train_m: dict[str, Any], val_m: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "trial": idx,
        "candidate_id": params.get("candidate_id", f"final_{idx:07d}"),
        "train_accuracy": train_m["accuracy"],
        "train_macro_f1": train_m["macro_f1"],
        "train_balanced_accuracy": train_m["balanced_accuracy"],
        "train_min_recall": train_m["min_recall"],
        "val_accuracy": val_m["accuracy"],
        "val_macro_f1": val_m["macro_f1"],
        "val_balanced_accuracy": val_m["balanced_accuracy"],
        "val_min_recall": val_m["min_recall"],
        "complexity": sum(1 for k, v in params.items() if k != "candidate_id" and v not in (False, None, 0, "")),
        "params_json": json.dumps(params, sort_keys=True, separators=(",", ":")),
    }
    for split_name, metric in [("train", train_m), ("val", val_m)]:
        for cls in CLASSES:
            row[f"{split_name}_{cls}_recall"] = metric["per_class"][cls]["recall"]
            row[f"{split_name}_{cls}_precision"] = metric["per_class"][cls]["precision"]
            row[f"{split_name}_{cls}_f1"] = metric["per_class"][cls]["f1"]
    return row


def sort_key(row: dict[str, Any]) -> tuple[float, float, float, float, float]:
    return (
        float(row["val_macro_f1"]),
        float(row["val_balanced_accuracy"]),
        float(row["val_min_recall"]),
        float(row["val_accuracy"]),
        -float(row["complexity"]),
    )


def write_summary(top_rows: list[dict[str, Any]], best_params: dict[str, Any], train_m: dict[str, Any], val_m: dict[str, Any], trial_count: int, max_trials: int) -> Any:
    path = REPORTS / "search" / "final_membrane_search_summary.md"
    lines = [
        "# Strict Record-wise Final Membrane Search Summary",
        "",
        f"- Trials evaluated: `{trial_count}`",
        f"- Max trial setting: `{max_trials}`",
        "- Search split scope: `train + validation only`",
        "- test_used_for_selection: `false`",
        f"- Best validation macro-F1: `{val_m['macro_f1']:.6f}`",
        f"- Best validation accuracy: `{val_m['accuracy']:.6f}`",
        "",
        "## Best Validation Per-class Recall",
        "",
        md_table(["class", "recall", "precision", "f1", "support"], [[cls, pct(float(val_m["per_class"][cls]["recall"])), pct(float(val_m["per_class"][cls]["precision"])), pct(float(val_m["per_class"][cls]["f1"])), val_m["per_class"][cls]["support"]] for cls in CLASSES]),
        "",
        "## Selected Final Membrane Params",
        "",
        "```json",
        json.dumps(best_params, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Top 10 Candidates",
        "",
        md_table(["rank", "candidate", "val_macro_f1", "val_accuracy", "val_min_recall", "complexity"], [[idx + 1, row["candidate_id"], f"{float(row['val_macro_f1']):.6f}", f"{float(row['val_accuracy']):.6f}", f"{float(row['val_min_recall']):.6f}", row["complexity"]] for idx, row in enumerate(top_rows[:10])]),
        "",
        "## Search Scope Limitation",
        "",
        "이 script는 기존 Python final membrane candidate grid에서 탐색 가능한 parameter subset을 대상으로 한다. RTL hardcoded feature extractor threshold와 ARR-focus post-search의 전체 random space는 inventory/TODO로 분리한다.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Search final membrane parameters on strict record-wise train/val only.")
    parser.add_argument("--resume", action="store_true", help="Accepted for workflow compatibility; current run rewrites deterministic trial log.")
    parser.add_argument("--max-trials", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()

    snapshot_payload = read_json(CONFIGS / "best_snapshot_params.json")
    snapshot_params = snapshot_payload["params"]
    split_rows = load_strict_split()
    rows = rows_with_snapshot_params(strict_rows_from_split(split_rows), snapshot_params)
    final_mod = load_final_module()
    chunks = chunks_by_split(final_mod, rows)
    train = chunks["train"]
    val = chunks["val"]
    if chunks["test"]:
        pass

    trial_path = REPORTS / "search" / "final_membrane_trials.jsonl"
    trial_path.parent.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, Any]] = []
    best: tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None = None
    candidates = final_mod.candidate_grid()
    if args.max_trials > 0:
        candidates = islice(candidates, args.max_trials)
    with trial_path.open("w", encoding="utf-8") as f:
        for idx, params in enumerate(candidates, 1):
            train_m, _, _ = evaluate(final_mod, train, params)
            val_m, _, _ = evaluate(final_mod, val, params)
            row = flatten(params, idx, train_m, val_m)
            rows_out.append(row)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if best is None or sort_key(row) > sort_key(flatten(best[0], -1, best[1], best[2])):
                best = (dict(params), train_m, val_m)
            if idx % 1000 == 0:
                print(f"final membrane trials {idx}", flush=True)
    if best is None:
        raise RuntimeError("no final membrane candidate evaluated")
    rows_out.sort(key=sort_key, reverse=True)
    top_path = REPORTS / "search" / "final_membrane_top_candidates.csv"
    write_csv(top_path, rows_out[: min(100, len(rows_out))])
    best_params, train_m, val_m = best
    best_path = CONFIGS / "best_final_membrane_params.json"
    write_json(
        best_path,
        {
            "selected_from": "strict record-wise train/validation final membrane search",
            "test_used_for_selection": False,
            "trial_count": len(rows_out),
            "params": best_params,
            "train_metrics": train_m,
            "val_metrics": val_m,
        },
    )
    split_payload = read_json(split_json_path(args.seed))
    record_lists = record_lists_from_split(split_rows)
    locked = {
        "selected_before_test_evaluation": True,
        "test_used_for_selection": False,
        "split_hash": split_payload.get("split_hash"),
        "train_record_list_hash": sha256_json(record_lists["train"]),
        "val_record_list_hash": sha256_json(record_lists["val"]),
        "test_record_list_hash": sha256_json(record_lists["test"]),
        "selection_metric": "validation macro-F1, balanced accuracy, min recall, accuracy, lower complexity tie-break",
        "selected_snapshot_params": snapshot_payload,
        "selected_final_membrane_params": {
            "params": best_params,
            "train_metrics": train_m,
            "val_metrics": val_m,
            "trial_count": len(rows_out),
        },
        "search_scope_note": "Existing Python final membrane grid searched. Some RTL feature thresholds and ARR-focus random-post-search parameters remain fixed/TODO; see parameter_inventory.md.",
    }
    locked_path = CONFIGS / "best_strict_recordwise_params_locked.json"
    write_json(locked_path, locked)
    summary = write_summary(rows_out, best_params, train_m, val_m, len(rows_out), args.max_trials)
    write_log("search_final_membrane_recordwise", sys.argv, [trial_path, top_path, best_path, locked_path, summary], {"test_used_for_selection": False, "trial_count": len(rows_out)})
    print(summary)


if __name__ == "__main__":
    main()
