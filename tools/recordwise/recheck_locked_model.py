#!/usr/bin/env python3
"""Re-evaluate the locked strict record-wise Final Membrane candidate.

This is a verification-only script. It does not search, rank, mutate the
locked JSON, or increment the one-time final_test evaluation counter.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


RUN_ID_ENV = "resplit_seed20260808"
os.environ["RECORDWISE_RUN_ID"] = RUN_ID_ENV

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from recordwise_common import (  # noqa: E402
    CLASSES,
    CONFIGS,
    REPO,
    load_final_module,
    load_strict_split,
    metric_from_pairs,
    pct,
    read_json,
    sha256_json,
    write_csv,
    write_json,
)
from search_final_membrane_huge_grid import source_record_by_case  # noqa: E402
from search_final_membrane_structural_grid import compact_chunk_rows, evaluate, load_base_context  # noqa: E402


FINAL_SUBMISSION = REPO / "reports" / "final_submission"
LOCKED_JSON = CONFIGS / "best_final_membrane_structural_grid_locked.json"
FINAL_TEST_METRICS = REPO / "reports" / "strict_recordwise_resplit_seed20260808" / "final_test_structural_grid_final_membrane" / "structural_final_test_metrics.json"
TEST_COUNT_JSON = REPO / "reports" / "strict_recordwise_resplit_seed20260808" / "final_test_structural_grid_final_membrane" / "test_evaluation_count.json"

OUT_MD = FINAL_SUBMISSION / "python_locked_model_recheck.md"
OUT_CSV = FINAL_SUBMISSION / "python_locked_model_predictions.csv"
OUT_JSON = FINAL_SUBMISSION / "python_locked_model_metrics.json"


EXPECTED = {
    "candidate": "structural_guarded_silent_aff_1008710",
    "train": (61, 68),
    "val": (32, 32),
    "test": (29, 36),
    "test_record_majority": (16, 19),
    "test_evaluation_count": 1,
}


def argmax4(values: list[int]) -> int:
    best = 0
    for idx in range(1, 4):
        if values[idx] > values[best]:
            best = idx
    return best


def correct_total(metric: dict[str, Any]) -> tuple[int, int]:
    return int(metric["correct"]), int(metric["total"])


def record_majority(
    rows: list[dict[str, Any]],
    predictions: dict[str, int],
    source_by_case: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[source_by_case[str(row["case_id"])]].append(row)

    true_ids: list[int] = []
    pred_ids: list[int] = []
    out_rows: list[dict[str, Any]] = []
    for source_record_id in sorted(grouped):
        items = grouped[source_record_id]
        votes = [0, 0, 0, 0]
        for row in items:
            votes[predictions[str(row["case_id"])]] += 1
        pred = argmax4(votes)
        truth = int(items[0]["class_id"])
        true_ids.append(truth)
        pred_ids.append(pred)
        out_rows.append(
            {
                "source_record_id": source_record_id,
                "class_label": CLASSES[truth],
                "pred_class": pred,
                "pred_label": CLASSES[pred],
                "correct": int(pred == truth),
                "chunk_count": len(items),
                "vote_NSR": votes[0],
                "vote_CHF": votes[1],
                "vote_ARR": votes[2],
                "vote_AFF": votes[3],
            }
        )
    return metric_from_pairs(true_ids, pred_ids), out_rows


def main() -> int:
    locked = read_json(LOCKED_JSON)
    params = locked["params"]
    candidate = locked.get("selected_candidate_id") or params.get("candidate_id")
    if candidate != EXPECTED["candidate"]:
        raise SystemExit(f"unexpected locked candidate: {candidate}")

    final_mod = load_final_module()
    split_rows = load_strict_split()
    source_by = source_record_by_case(split_rows)
    chunks, base, _base_lock = load_base_context(final_mod, ["train", "val", "test"])
    compact = compact_chunk_rows(chunks, base)

    metrics: dict[str, Any] = {
        "candidate": candidate,
        "locked_params_hash": sha256_json(params),
        "final_test_used_for_selection": bool(locked.get("test_used_for_selection", True)),
        "final_test_used_for_parameter_search": bool(locked.get("test_used_for_parameter_search", True)),
        "final_test_used_for_chatgpt_context": bool(locked.get("test_used_for_chatgpt_context", True)),
    }

    prediction_rows: list[dict[str, Any]] = []
    predictions_by_split: dict[str, dict[str, int]] = {}
    details_by_split: dict[str, dict[str, dict[str, Any]]] = {}
    for split in ["train", "val", "test"]:
        metric, predictions, details = evaluate(compact[split], chunks[split], final_mod, params)
        metrics[split] = metric
        predictions_by_split[split] = predictions
        details_by_split[split] = details
        for row in compact[split]:
            cid = str(row["case_id"])
            pred = predictions[cid]
            detail = details[cid]
            prediction_rows.append(
                {
                    "split": split,
                    "case_id": cid,
                    "source_record_id": source_by.get(cid, ""),
                    "class_label": row["class_label"],
                    "class_id": row["class_id"],
                    "record_id": row["record_id"],
                    "chunk_id": row["chunk_id"],
                    "chunk_file": row["chunk_file"],
                    "pred_class": pred,
                    "pred_label": CLASSES[pred],
                    "correct": int(pred == int(row["class_id"])),
                    "final_mem_NSR": detail["final_mem_NSR"],
                    "final_mem_CHF": detail["final_mem_CHF"],
                    "final_mem_ARR": detail["final_mem_ARR"],
                    "final_mem_AFF": detail["final_mem_AFF"],
                    "aff_persistence_gate": detail["aff_persistence_gate"],
                    "nsr_clean_chf_gate": detail["nsr_clean_chf_gate"],
                    "arr_over_nsr_gate": detail["arr_over_nsr_gate"],
                    "arr_over_aff_gate": detail["arr_over_aff_gate"],
                    "aff_silent_dropout_gate": detail["aff_silent_dropout_gate"],
                }
            )

    test_record_metric, record_rows = record_majority(compact["test"], predictions_by_split["test"], source_by)
    metrics["test_record_majority"] = test_record_metric

    test_eval_count = read_json(TEST_COUNT_JSON) if TEST_COUNT_JSON.exists() else {}
    previous_final_test = read_json(FINAL_TEST_METRICS) if FINAL_TEST_METRICS.exists() else {}
    metrics["test_evaluation_count"] = test_eval_count.get("test_evaluation_count")
    metrics["previous_final_test_artifact"] = str(FINAL_TEST_METRICS.relative_to(REPO)) if FINAL_TEST_METRICS.exists() else None
    metrics["matches_expected"] = {
        "train": correct_total(metrics["train"]) == EXPECTED["train"],
        "val": correct_total(metrics["val"]) == EXPECTED["val"],
        "test": correct_total(metrics["test"]) == EXPECTED["test"],
        "test_record_majority": correct_total(metrics["test_record_majority"]) == EXPECTED["test_record_majority"],
        "test_evaluation_count": metrics["test_evaluation_count"] == EXPECTED["test_evaluation_count"],
        "test_artifact_candidate": previous_final_test.get("selected_candidate_id") in (None, candidate),
    }

    FINAL_SUBMISSION.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_CSV, prediction_rows)
    write_json(OUT_JSON, metrics)

    rows = []
    for key, label in [
        ("train", "Train"),
        ("val", "Validation"),
        ("test", "Final test chunk"),
        ("test_record_majority", "Final test record-majority"),
    ]:
        correct, total = correct_total(metrics[key])
        rows.append(f"| {label} | {correct}/{total} | {pct(correct / total if total else 0.0)} |")

    checks = metrics["matches_expected"]
    md = [
        "# Python Locked Model Recheck",
        "",
        "이 파일은 locked JSON을 다시 읽어 Python golden prediction을 재생성한 확인 결과이다.",
        "검색/선택을 다시 수행하지 않았고, final_test evaluation counter를 증가시키지 않았다.",
        "",
        "| 항목 | 값 |",
        "|---|---|",
        f"| candidate | `{candidate}` |",
        f"| locked_params_hash | `{metrics['locked_params_hash']}` |",
        f"| final_test_used_for_selection | `{metrics['final_test_used_for_selection']}` |",
        f"| final_test_used_for_parameter_search | `{metrics['final_test_used_for_parameter_search']}` |",
        f"| final_test_used_for_chatgpt_context | `{metrics['final_test_used_for_chatgpt_context']}` |",
        f"| test_evaluation_count | `{metrics['test_evaluation_count']}` |",
        "",
        "## Metrics",
        "",
        "| level | correct/total | accuracy |",
        "|---|---:|---:|",
        *rows,
        "",
        "## Expected Artifact Match",
        "",
        "| check | result |",
        "|---|---|",
        *[f"| {key} | `{value}` |" for key, value in checks.items()],
        "",
        "## Outputs",
        "",
        f"- predictions: `{OUT_CSV.relative_to(REPO)}`",
        f"- metrics JSON: `{OUT_JSON.relative_to(REPO)}`",
        f"- previous one-time final_test artifact: `{FINAL_TEST_METRICS.relative_to(REPO)}`",
        "",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8", newline="\n")
    if not all(checks.values()):
        raise SystemExit("locked Python recheck does not match expected artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
