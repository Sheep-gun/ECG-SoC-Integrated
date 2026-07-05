from __future__ import annotations

import argparse
import csv
import heapq
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    confusion_rows,
    load_final_module,
    load_strict_split,
    md_table,
    metric_from_pairs,
    pct,
    read_json,
    sha256_json,
    split_json_path,
    strict_rows_from_split,
    write_csv,
    write_json,
    write_log,
)
from search_final_membrane_huge_grid import (
    artifact_manifest,
    assert_artifact_manifest,
    frontend_subset_hash,
    load_chunks_by_split,
)


OUT = REPORTS / "structural_grid_final_membrane"
FINAL_TEST_OUT = REPORTS / "final_test_structural_grid_final_membrane"
BASE_LOCKED_PARAMS = CONFIGS / "best_final_membrane_snn_huge_grid_locked.json"
LOCKED_PARAMS = CONFIGS / "best_final_membrane_structural_grid_locked.json"
FINAL_TEST_LOCK = CONFIGS / "final_test_records_locked.json"

MIN_TRAIN_CORRECT = 61
MIN_VAL_CORRECT = 30
RANDOM_SEED = 5610808


def argmax4(values: list[int]) -> int:
    best = 0
    for idx in range(1, 4):
        if values[idx] > values[best]:
            best = idx
    return best


def load_base_context(final_mod: Any, target_splits: list[str]) -> tuple[dict[str, list[Any]], dict[str, tuple[dict[str, int], dict[str, dict[str, Any]]]], dict[str, Any]]:
    if not BASE_LOCKED_PARAMS.exists():
        raise SystemExit(f"base locked params missing: {BASE_LOCKED_PARAMS}")
    base_lock = read_json(BASE_LOCKED_PARAMS)
    base_params = base_lock["params"]
    chunks = load_chunks_by_split(final_mod, target_splits=target_splits)
    base: dict[str, tuple[dict[str, int], dict[str, dict[str, Any]]]] = {}
    for split in target_splits:
        base[split] = final_mod.apply_candidate(chunks[split], base_params)
    return chunks, base, base_lock


def compact_chunk_rows(chunks: dict[str, list[Any]], base: dict[str, tuple[dict[str, int], dict[str, dict[str, Any]]]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for split, split_chunks in chunks.items():
        _, details = base[split]
        rows: list[dict[str, Any]] = []
        for chunk in split_chunks:
            fs = chunk.feature_sum
            rows.append(
                {
                    "case_id": chunk.case_id,
                    "class_id": chunk.class_id,
                    "class_label": chunk.class_label,
                    "record_id": chunk.record_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_file": chunk.chunk_file,
                    "counts": list(chunk.pred_count),
                    "base_mem": [int(details[chunk.case_id][f"final_mem_{cls}"]) for cls in CLASSES],
                    "qrs": int(fs["qrs_maf_count"]),
                    "ect": int(fs["ectopic_pair_count"]),
                    "morph": int(fs["morphology_evidence_count"]),
                    "rhythm": int(fs["rhythm_irregular_evidence_count"]),
                    "pre": int(fs["pre_qrs_bump_count"]),
                    "abn": int(fs["abnormal_evidence_count"]),
                    "rbbb": int(fs["rbbb_delay_like_count"]),
                    "beat": int(fs["beat_count"]),
                    "ram": int(fs["ram_code_sum"]),
                    "rdm_valid": int(fs["rdm_valid_count"]),
                    "rdm_sum": int(fs["rdm_code_sum"]),
                }
            )
        out[split] = rows
    return out


RANGES: dict[str, list[int]] = {
    "aff_cnt": [12, 14, 16, 18],
    "aff_chf_cnt": [8, 10, 12, 14],
    "aff_morph_le": [150, 300, 600, 1000, 2000, 3000],
    "aff_rhythm_ge": [8000, 12000, 16000, 19000],
    "aff_qrs_le": [80, 150, 300, 600, 1000],
    "nsr_cnt": [4, 6, 8, 10, 12],
    "nsr_chf_cnt": [8, 12, 16, 20],
    "nsr_morph_le": [10, 20, 50, 100, 200],
    "nsr_abn_le": [30, 60, 120, 250],
    "nsr_qrs_le": [2, 5, 10, 30, 80],
    "nsr_ect_le": [10, 20, 40, 80],
    "arr_nsr_nsr_cnt": [16, 18, 20, 22, 24, 27, 29],
    "arr_nsr_morph_ge": [3000, 3500, 4000, 4500, 5000, 5500],
    "arr_nsr_pre_ge": [1600, 2000, 2200, 2400, 2600, 2800],
    "arr_nsr_arr_cnt": [1, 2, 3, 4, 5, 6],
    "arr_nsr_qrs_high_le": [40, 60, 80, 100],
    "arr_nsr_rbbb_high_le": [0, 8, 16, 20],
    "arr_nsr_arr_low_le": [0, 1, 2],
    "arr_nsr_qrs_low_le": [5, 30, 80],
    "arr_nsr_ect_low_le": [5, 20, 40, 80],
    "arr_nsr_rhythm_low_le": [3500, 4000, 5000, 6000, 7000, 10000],
    "arr_aff_aff_cnt": [8, 10, 14, 18, 20],
    "arr_aff_arr_cnt": [3, 5, 7, 9, 12, 14],
    "arr_aff_morph_ge": [500, 1000, 2000, 3000, 4000],
    "arr_aff_ect_ge": [50, 100, 250, 400, 600],
    "arr_aff_qrs_le": [100, 200, 300, 500, 800],
    "aff_boost": [40, 60, 80, 120],
    "aff_inh_chf": [40, 60, 80, 120],
    "aff_inh_arr": [0, 10, 20, 40],
    "nsr_boost": [40, 60, 80, 120],
    "nsr_inh_chf": [40, 60, 80, 120],
    "nsr_inh_arr": [0, 10, 20, 40],
    "arr_nsr_boost": [40, 60, 80, 120],
    "arr_nsr_inh_nsr": [40, 60, 80, 120],
    "arr_nsr_inh_chf": [0, 10, 20, 40],
    "arr_nsr_inh_aff": [0, 10, 20, 40],
    "arr_aff_boost": [40, 60, 80, 120],
    "arr_aff_inh_aff": [40, 60, 80, 120],
}


def sampled_params(rng: random.Random) -> dict[str, int]:
    return {key: rng.choice(values) for key, values in RANGES.items()}


def predict_structural(row: dict[str, Any], params: dict[str, int]) -> tuple[int, list[int], dict[str, int]]:
    counts = row["counts"]
    mem = list(row["base_mem"])
    qrs = row["qrs"]
    ect = row["ect"]
    morph = row["morph"]
    rhythm = row["rhythm"]
    pre = row["pre"]
    abn = row["abn"]
    rbbb = row["rbbb"]
    beat = row["beat"]
    ram = row["ram"]
    flags = {
        "aff_persistence_gate": 0,
        "nsr_clean_chf_gate": 0,
        "arr_over_nsr_gate": 0,
        "arr_over_aff_gate": 0,
        "aff_silent_dropout_gate": 0,
    }

    if (
        counts[3] >= params["aff_cnt"]
        and counts[1] >= params["aff_chf_cnt"]
        and morph <= params["aff_morph_le"]
        and rhythm >= params["aff_rhythm_ge"]
        and qrs <= params["aff_qrs_le"]
    ):
        flags["aff_persistence_gate"] = 1
        mem[3] += params["aff_boost"]
        mem[1] -= params["aff_inh_chf"]
        mem[2] -= params["aff_inh_arr"]

    if (
        counts[0] >= params["nsr_cnt"]
        and counts[1] >= params["nsr_chf_cnt"]
        and morph <= params["nsr_morph_le"]
        and abn <= params["nsr_abn_le"]
        and qrs <= params["nsr_qrs_le"]
        and ect <= params["nsr_ect_le"]
    ):
        flags["nsr_clean_chf_gate"] = 1
        mem[0] += params["nsr_boost"]
        mem[1] -= params["nsr_inh_chf"]
        mem[2] -= params["nsr_inh_arr"]

    arr_over_nsr = False
    if counts[0] >= params["arr_nsr_nsr_cnt"] and morph >= params["arr_nsr_morph_ge"] and pre >= params["arr_nsr_pre_ge"]:
        if counts[2] >= params["arr_nsr_arr_cnt"] and qrs <= params["arr_nsr_qrs_high_le"] and rbbb <= params["arr_nsr_rbbb_high_le"]:
            arr_over_nsr = True
        elif (
            counts[2] <= params["arr_nsr_arr_low_le"]
            and qrs <= params["arr_nsr_qrs_low_le"]
            and ect <= params["arr_nsr_ect_low_le"]
            and rhythm <= params["arr_nsr_rhythm_low_le"]
        ):
            arr_over_nsr = True
    if arr_over_nsr:
        flags["arr_over_nsr_gate"] = 1
        mem[2] += params["arr_nsr_boost"]
        mem[0] -= params["arr_nsr_inh_nsr"]
        mem[1] -= params["arr_nsr_inh_chf"]
        mem[3] -= params["arr_nsr_inh_aff"]

    if (
        counts[3] >= params["arr_aff_aff_cnt"]
        and counts[2] >= params["arr_aff_arr_cnt"]
        and morph >= params["arr_aff_morph_ge"]
        and ect >= params["arr_aff_ect_ge"]
        and qrs <= params["arr_aff_qrs_le"]
    ):
        flags["arr_over_aff_gate"] = 1
        mem[2] += params["arr_aff_boost"]
        mem[3] -= params["arr_aff_inh_aff"]

    # Silent low-evidence AFF dropout recovery: an SNN-style rescue neuron for
    # chunks where the snapshot frontend collapses to CHF despite nearly no
    # beat/evidence activity. This gate is selected on train/validation only.
    if (
        counts[1] >= 29
        and counts[0] <= 1
        and counts[2] == 0
        and counts[3] == 0
        and beat <= 10
        and morph <= 8
        and rhythm <= 20
        and abn <= 10
        and qrs <= 3
        and ect == 0
        and ram == 0
    ):
        flags["aff_silent_dropout_gate"] = 1
        mem[3] += 120
        mem[1] -= 120

    return argmax4(mem), mem, flags


def evaluate(rows: list[dict[str, Any]], chunks: list[Any], final_mod: Any, params: dict[str, int]) -> tuple[dict[str, Any], dict[str, int], dict[str, dict[str, Any]]]:
    predictions: dict[str, int] = {}
    details: dict[str, dict[str, Any]] = {}
    for row in rows:
        pred, mem, flags = predict_structural(row, params)
        case_id = str(row["case_id"])
        predictions[case_id] = pred
        details[case_id] = {
            "final_mem_NSR": mem[0],
            "final_mem_CHF": mem[1],
            "final_mem_ARR": mem[2],
            "final_mem_AFF": mem[3],
            **flags,
        }
    return final_mod.metric_for_predictions(chunks, predictions), predictions, details


def rank_key(train_m: dict[str, Any], val_m: dict[str, Any], params: dict[str, int]) -> tuple[Any, ...]:
    return (
        int(val_m["correct"]),
        int(train_m["correct"]),
        float(val_m["macro_f1"]),
        float(train_m["macro_f1"]),
        float(val_m["min_recall"]),
        float(train_m["min_recall"]),
        -sum(abs(v) for k, v in params.items() if k.endswith(("boost", "inh_chf", "inh_arr", "inh_nsr", "inh_aff"))),
    )


def push_top(heap: list[tuple[Any, int, dict[str, int], dict[str, Any], dict[str, Any]]], item: tuple[Any, int, dict[str, int], dict[str, Any], dict[str, Any]], limit: int) -> None:
    if len(heap) < limit:
        heapq.heappush(heap, item)
    elif item[0] > heap[0][0]:
        heapq.heapreplace(heap, item)


def write_summary(path: Path, payload: dict[str, Any], top_rows: list[dict[str, Any]]) -> None:
    train = payload["train_metrics"]
    val = payload["val_metrics"]
    lines = [
        "# Strict Record-wise Structural Final Membrane Search",
        "",
        "- Stage A: train/validation only",
        "- ChatGPT 5.5 Pro session: `" + payload.get("chatgpt_55pro_session", "") + "`",
        "- Final-test used for structure selection: `false`",
        "- Final-test used for parameter search: `false`",
        f"- Random seed: `{payload['random_seed']}`",
        f"- Candidates evaluated: `{payload['candidate_count']}`",
        f"- Passing candidates train>=61/68 and validation>=30/32: `{payload['passing_candidate_count']}`",
        f"- Selected candidate: `{payload['selected_candidate_id']}`",
        "",
        md_table(
            ["split", "correct/total", "accuracy", "macro-F1", "balanced accuracy"],
            [
                ["train", f"{train['correct']}/{train['total']}", pct(train["accuracy"]), pct(train["macro_f1"]), pct(train["balanced_accuracy"])],
                ["validation", f"{val['correct']}/{val['total']}", pct(val["accuracy"]), pct(val["macro_f1"]), pct(val["balanced_accuracy"])],
            ],
        ),
        "",
        "## Top Candidates",
        "",
        md_table(
            ["rank", "candidate", "train", "validation", "val_macro_f1", "train_macro_f1"],
            [
                [
                    idx + 1,
                    row["candidate_id"],
                    row["train_correct"],
                    row["val_correct"],
                    row["val_macro_f1"],
                    row["train_macro_f1"],
                ]
                for idx, row in enumerate(top_rows[:20])
            ],
        ),
        "",
        "## Selected Params",
        "",
        "```json",
        json.dumps(payload["params"], indent=2, ensure_ascii=False),
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def command_search(args: argparse.Namespace) -> None:
    if not FINAL_TEST_LOCK.exists():
        raise SystemExit(f"final_test lock missing: {FINAL_TEST_LOCK}")
    final_mod = load_final_module()
    chunks, base, base_lock = load_base_context(final_mod, ["train", "val"])
    compact_rows = compact_chunk_rows(chunks, base)
    split_payload = read_json(split_json_path(args.seed))
    split_rows = load_strict_split()
    frontend_hashes = frontend_subset_hash(split_rows, ["train", "val"])
    rng = random.Random(args.random_seed)
    top_heap: list[tuple[Any, int, dict[str, int], dict[str, Any], dict[str, Any]]] = []
    passing = 0
    best_item: tuple[Any, int, dict[str, int], dict[str, Any], dict[str, Any]] | None = None
    OUT.mkdir(parents=True, exist_ok=True)

    for trial in range(1, args.iterations + 1):
        params = sampled_params(rng)
        train_m, _, _ = evaluate(compact_rows["train"], chunks["train"], final_mod, params)
        val_m, _, _ = evaluate(compact_rows["val"], chunks["val"], final_mod, params)
        key = rank_key(train_m, val_m, params)
        item = (key, trial, params, train_m, val_m)
        push_top(top_heap, item, args.top)
        if int(train_m["correct"]) >= MIN_TRAIN_CORRECT and int(val_m["correct"]) >= MIN_VAL_CORRECT:
            passing += 1
            if best_item is None or key > best_item[0]:
                best_item = item
        if trial % args.progress_every == 0:
            top = max(top_heap, key=lambda x: x[0])
            print(
                f"structural {trial} candidates; top train={top[3]['correct']}/{top[3]['total']} "
                f"val={top[4]['correct']}/{top[4]['total']} passing={passing}",
                flush=True,
            )

    selected = best_item if best_item is not None else max(top_heap, key=lambda x: x[0])
    _, selected_trial, params, train_m, val_m = selected
    train_m2, train_pred, train_details = evaluate(compact_rows["train"], chunks["train"], final_mod, params)
    val_m2, val_pred, val_details = evaluate(compact_rows["val"], chunks["val"], final_mod, params)
    assert train_m2["correct"] == train_m["correct"]
    assert val_m2["correct"] == val_m["correct"]

    candidate_id = f"structural_guarded_silent_aff_{selected_trial:07d}"
    params = dict(params)
    params["candidate_id"] = candidate_id
    params["family"] = "F1_F6_F10_guarded_rescue_silent_aff"
    lock_payload = {
        "selected_before_test_evaluation": True,
        "test_used_for_selection": False,
        "test_used_for_parameter_search": False,
        "test_used_for_chatgpt_context": False,
        "split_hash": split_payload["split_hash"],
        "final_test_lock_path": str(FINAL_TEST_LOCK),
        "final_test_lock_artifact": artifact_manifest([FINAL_TEST_LOCK]),
        "base_locked_params_path": str(BASE_LOCKED_PARAMS),
        "base_locked_params_hash": sha256_json(base_lock["params"]),
        "fixed_frontend_subset_hashes": frontend_hashes,
        "search_script_artifacts": artifact_manifest([Path(__file__).resolve()]),
        "chatgpt_55pro_session": args.chatgpt_session,
        "random_seed": args.random_seed,
        "candidate_count": args.iterations,
        "passing_candidate_count": passing,
        "target": {"train_correct_ge": MIN_TRAIN_CORRECT, "val_correct_ge": MIN_VAL_CORRECT},
        "selected_candidate_id": candidate_id,
        "selected_trial": selected_trial,
        "selected_candidate_params_hash": sha256_json(params),
        "params": params,
        "train_metrics": train_m2,
        "val_metrics": val_m2,
    }
    write_json(LOCKED_PARAMS, lock_payload)
    write_json(OUT / "structural_grid_search_summary.json", lock_payload)
    top_items = sorted(top_heap, key=lambda x: x[0], reverse=True)
    top_rows: list[dict[str, Any]] = []
    for idx, (_, trial, top_params, top_train, top_val) in enumerate(top_items, 1):
        top_rows.append(
            {
                "rank": idx,
                "candidate_id": f"structural_guarded_silent_aff_{trial:07d}",
                "trial": trial,
                "train_correct": f"{top_train['correct']}/{top_train['total']}",
                "val_correct": f"{top_val['correct']}/{top_val['total']}",
                "train_accuracy": top_train["accuracy"],
                "val_accuracy": top_val["accuracy"],
                "train_macro_f1": top_train["macro_f1"],
                "val_macro_f1": top_val["macro_f1"],
                "params_json": json.dumps(top_params, sort_keys=True, separators=(",", ":")),
            }
        )
    write_csv(OUT / "structural_grid_top_candidates.csv", top_rows)
    write_summary(OUT / "structural_grid_search_summary.md", lock_payload, top_rows)
    write_log(
        "search_final_membrane_structural_grid",
        sys.argv,
        [LOCKED_PARAMS, OUT / "structural_grid_search_summary.json", OUT / "structural_grid_search_summary.md", OUT / "structural_grid_top_candidates.csv"],
        {"candidate_count": args.iterations, "passing_candidate_count": passing, "selected_candidate_id": candidate_id},
    )
    print(
        f"selected {candidate_id} train={train_m2['correct']}/{train_m2['total']} "
        f"val={val_m2['correct']}/{val_m2['total']} passing={passing}",
        flush=True,
    )


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, int], details: dict[str, dict[str, Any]], source_by_case: dict[str, str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        case_id = str(row["case_id"])
        pred = predictions[case_id]
        out_row = {
            "case_id": case_id,
            "source_record_id": source_by_case.get(case_id, ""),
            "class_label": row["class_label"],
            "class_id": row["class_id"],
            "record_id": row["record_id"],
            "chunk_id": row["chunk_id"],
            "chunk_file": row["chunk_file"],
            "pred_class": pred,
            "pred_label": CLASSES[pred],
            "correct": int(pred == int(row["class_id"])),
        }
        out_row.update(details[case_id])
        out.append(out_row)
    return out


def record_level(pred_rows: list[dict[str, Any]]) -> tuple[list[int], list[int], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in pred_rows:
        grouped.setdefault(row["source_record_id"], []).append(row)
    true_ids: list[int] = []
    pred_ids: list[int] = []
    rows: list[dict[str, Any]] = []
    for record, items in sorted(grouped.items()):
        cls_id = int(items[0]["class_id"])
        counts = [0, 0, 0, 0]
        for item in items:
            counts[int(item["pred_class"])] += 1
        pred = argmax4(counts)
        true_ids.append(cls_id)
        pred_ids.append(pred)
        rows.append(
            {
                "source_record_id": record,
                "class_label": CLASSES[cls_id],
                "pred_class": pred,
                "pred_label": CLASSES[pred],
                "correct": int(pred == cls_id),
                "chunk_count": len(items),
                "vote_NSR": counts[0],
                "vote_CHF": counts[1],
                "vote_ARR": counts[2],
                "vote_AFF": counts[3],
            }
        )
    return true_ids, pred_ids, rows


def write_final_test_summary(path: Path, payload: dict[str, Any]) -> None:
    chunk = payload["chunk_level"]
    rec = payload["record_level_majority"]
    lines = [
        "# Strict Record-wise Structural Final Membrane Final Test",
        "",
        f"- test_evaluation_count: `{payload['test_evaluation_count']}`",
        f"- Split hash: `{payload['split_hash']}`",
        "- Test used for selection: `false`",
        "",
        md_table(
            ["level", "correct/total", "accuracy", "macro-F1", "balanced accuracy"],
            [
                ["chunk", f"{chunk['correct']}/{chunk['total']}", pct(chunk["accuracy"]), pct(chunk["macro_f1"]), pct(chunk["balanced_accuracy"])],
                ["record-majority", f"{rec['correct']}/{rec['total']}", pct(rec["accuracy"]), pct(rec["macro_f1"]), pct(rec["balanced_accuracy"])],
            ],
        ),
        "",
        "## Per-class Chunk Recall",
        "",
        md_table(
            ["class", "recall", "precision", "f1", "support"],
            [
                [
                    cls,
                    pct(float(chunk["per_class"][cls]["recall"])),
                    pct(float(chunk["per_class"][cls]["precision"])),
                    pct(float(chunk["per_class"][cls]["f1"])),
                    chunk["per_class"][cls]["support"],
                ]
                for cls in CLASSES
            ],
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def command_final_test(args: argparse.Namespace) -> None:
    if not LOCKED_PARAMS.exists():
        raise SystemExit(f"locked structural params missing: {LOCKED_PARAMS}")
    count_path = FINAL_TEST_OUT / "test_evaluation_count.json"
    locked = read_json(LOCKED_PARAMS)
    if count_path.exists() and not args.allow_rerun:
        raise SystemExit(f"structural final test already evaluated: {count_path}")
    final_mod = load_final_module()
    chunks, base, _ = load_base_context(final_mod, ["test"])
    compact_rows = compact_chunk_rows(chunks, base)
    params = locked["params"]
    test_m, test_pred, test_details = evaluate(compact_rows["test"], chunks["test"], final_mod, params)
    split_rows = load_strict_split()
    source_by_case = {str(row["strict_case_id"]): row["source_record_id"] for row in split_rows if row["split"] == "test"}
    pred_rows = prediction_rows(compact_rows["test"], test_pred, test_details, source_by_case)
    rec_true, rec_pred, rec_rows = record_level(pred_rows)
    rec_metric = metric_from_pairs(rec_true, rec_pred)
    eval_count = 1
    if count_path.exists():
        eval_count = int(read_json(count_path).get("test_evaluation_count", 0)) + 1
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_evaluation_count": eval_count,
        "split_hash": locked["split_hash"],
        "test_used_for_selection": False,
        "locked_params_path": str(LOCKED_PARAMS),
        "selected_candidate_id": locked["selected_candidate_id"],
        "chunk_level": test_m,
        "record_level_majority": rec_metric,
        "test_chunk_count_by_class": dict(Counter(row["class_label"] for row in pred_rows)),
        "test_record_count_by_class": dict(Counter(row["class_label"] for row in rec_rows)),
    }
    FINAL_TEST_OUT.mkdir(parents=True, exist_ok=True)
    write_csv(FINAL_TEST_OUT / "structural_final_test_predictions.csv", pred_rows)
    write_csv(FINAL_TEST_OUT / "structural_final_test_record_predictions.csv", rec_rows)
    write_csv(FINAL_TEST_OUT / "structural_final_test_confusion_matrix.csv", confusion_rows(test_m))
    write_json(FINAL_TEST_OUT / "structural_final_test_metrics.json", payload)
    write_json(count_path, {"test_evaluation_count": eval_count, "timestamp_utc": payload["timestamp_utc"], "split_hash": locked["split_hash"]})
    write_final_test_summary(FINAL_TEST_OUT / "structural_final_test_summary.md", payload)
    write_log(
        "evaluate_structural_final_membrane_test_once",
        sys.argv,
        [
            FINAL_TEST_OUT / "structural_final_test_predictions.csv",
            FINAL_TEST_OUT / "structural_final_test_record_predictions.csv",
            FINAL_TEST_OUT / "structural_final_test_metrics.json",
            FINAL_TEST_OUT / "structural_final_test_summary.md",
            count_path,
        ],
        {"test_evaluation_count": eval_count, "selected_candidate_id": locked["selected_candidate_id"]},
    )
    print(f"structural final-test {test_m['correct']}/{test_m['total']} macro_f1={test_m['macro_f1']:.4f}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train/validation-only structural final membrane search.")
    sub = parser.add_subparsers(required=True)
    search = sub.add_parser("search")
    search.add_argument("--seed", type=int, default=20260808)
    search.add_argument("--iterations", type=int, default=3_000_000)
    search.add_argument("--random-seed", type=int, default=RANDOM_SEED)
    search.add_argument("--progress-every", type=int, default=100_000)
    search.add_argument("--top", type=int, default=64)
    search.add_argument("--chatgpt-session", default="")
    search.set_defaults(func=command_search)
    test = sub.add_parser("final-test")
    test.add_argument("--allow-rerun", action="store_true")
    test.set_defaults(func=command_final_test)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
