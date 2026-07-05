from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import chain
from pathlib import Path
from typing import Any, Iterable

from recordwise_common import (
    CLASSES,
    CONFIGS,
    REPORTS,
    REPO,
    RESULTS,
    SPLITS,
    confusion_rows,
    load_final_module,
    load_strict_split,
    md_table,
    metric_from_pairs,
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


OUT = REPORTS / "huge_grid_snn_membrane"
FINAL_TEST_OUT = REPORTS / "final_test_snn_membrane_huge_grid"
LOCKED_PARAMS = CONFIGS / "best_final_membrane_snn_huge_grid_locked.json"
FIXED_SNAPSHOT = CONFIGS / "fixed_snapshot_for_final_membrane_snn_huge_grid.json"

ACTIVE_MEMBRANE_FIELDS = [
    "arr_boost",
    "arr_inhibit_nsr",
    "arr_inhibit_chf",
    "arr_inhibit_aff",
    "arr_aff_boost",
    "arr_aff_aff_inh",
    "arr_low_boost",
    "arr_low_inhibit_nsr",
    "arr_low_inhibit_chf",
    "arr_low_inhibit_aff",
    "arr_silent_boost",
    "arr_silent_inhibit_nsr",
    "aff_boost",
    "aff_inhibit_chf",
    "aff_inhibit_arr",
    "aff_boundary_boost",
    "aff_boundary_inhibit_arr",
    "aff_low_boost",
    "aff_low_inhibit_chf",
    "nsr_from_chf_boost",
    "nsr_from_chf_inhibit_chf",
    "chf_from_aff_boost",
    "chf_from_aff_inhibit_aff",
    "strong_nsr_boost",
    "strong_nsr_inhibit_arr",
    "strong_chf_boost",
    "strong_chf_inhibit_aff",
]


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(resolved)


def artifact_manifest(paths: Iterable[Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        out.append({"path": rel_path(path), "bytes": path.stat().st_size, "sha256": file_sha256(path)})
    return out


def assert_artifact_manifest(manifest: list[dict[str, Any]], label: str) -> None:
    for item in manifest:
        path = REPO / str(item["path"])
        if not path.exists():
            raise RuntimeError(f"{label} artifact missing: {path}")
        got = file_sha256(path)
        if got != item["sha256"]:
            raise RuntimeError(f"{label} artifact hash mismatch: {path} expected={item['sha256']} got={got}")


def frontend_artifact_manifest() -> list[dict[str, Any]]:
    return artifact_manifest(
        [
            RESULTS / "window_dump_train.csv",
            RESULTS / "window_dump_val.csv",
            RESULTS / "window_dump_test.csv",
            REPO / "scripts" / "search_final_membrane_v2_snn.py",
        ]
    )


def search_script_manifest() -> list[dict[str, Any]]:
    return artifact_manifest([Path(__file__).resolve(), REPO / "tools" / "recordwise" / "recordwise_common.py"])


def argmax(values: list[int]) -> int:
    best = 0
    for idx in range(1, len(values)):
        if values[idx] > values[best]:
            best = idx
    return best


def neutral_params() -> dict[str, Any]:
    return {
        "candidate_id": "neutral_majority_baseline",
        "base_from": "majority",
        "use_mem": "none",
        "vote_shift": 0,
        "mem_shift": 24,
        "bias_NSR": 0,
        "bias_CHF": 0,
        "bias_ARR": 0,
        "bias_AFF": 0,
        "strong_nsr_count_ge": 99,
        "strong_chf_count_ge": 99,
        "strong_nsr_margin_ge": 99,
        "strong_chf_margin_ge": 99,
        "strong_nsr_morph_le": 0,
        "strong_nsr_qrs_le": 0,
        "strong_nsr_boost": 0,
        "strong_nsr_inhibit_arr": 0,
        "strong_chf_boost": 0,
        "strong_chf_inhibit_aff": 0,
        "aff_boundary_count_ge": 99,
        "arr_aff_margin_le": -99,
        "aff_pnn_ge": 999999,
        "aff_rbbb_le": -1,
        "aff_boundary_boost": 0,
        "aff_boundary_inhibit_arr": 0,
        "aff_low_enable": 0,
        "aff_low_abn_le": 0,
        "aff_low_morph_le": 0,
        "aff_low_rbbb_le": 0,
        "aff_low_rdm_ge": 99,
        "aff_low_chf_count_ge": 99,
        "aff_low_boost": 0,
        "aff_low_inhibit_chf": 0,
        "arr_aff_arr_count_ge": 99,
        "arr_aff_qrs_ge": 999999,
        "arr_aff_morph_ge": 999999,
        "arr_aff_boost": 0,
        "arr_aff_aff_inh": 0,
        "aff_block_arr_count_ge": 99,
        "aff_count_ge": 99,
        "aff_chf_margin_le": -99,
        "aff_rhythm_ge": 999999,
        "aff_ecp_ge": 999999,
        "aff_boost": 0,
        "aff_inhibit_chf": 0,
        "aff_inhibit_arr": 0,
        "arr_count_ge": 99,
        "arr_nsr_margin_le": -99,
        "arr_morph_ge": 999999,
        "arr_qrs_ge": 999999,
        "arr_rbbb_ge": 999999,
        "arr_pre_ge": 999999,
        "arr_boost": 0,
        "arr_inhibit_nsr": 0,
        "arr_inhibit_chf": 0,
        "arr_inhibit_aff": 0,
        "arr_low_count_ge": 99,
        "arr_low_pre_ge": 999999,
        "arr_low_qrs_ge": 999999,
        "arr_low_rbbb_ge": 999999,
        "arr_low_morph_ge": 999999,
        "arr_low_abn_ge": 999999,
        "arr_low_boost": 0,
        "arr_low_inhibit_nsr": 0,
        "arr_low_inhibit_chf": 0,
        "arr_low_inhibit_aff": 0,
        "nsr_from_chf_nsr_count_ge": 99,
        "nsr_from_chf_abn_le": 0,
        "nsr_from_chf_qrs_le": 0,
        "nsr_from_chf_rbbb_le": 0,
        "nsr_from_chf_morph_le": 0,
        "nsr_from_chf_boost": 0,
        "nsr_from_chf_inhibit_chf": 0,
        "chf_from_aff_chf_count_ge": 99,
        "chf_from_aff_morph_le": 0,
        "chf_from_aff_qrs_le": 0,
        "chf_from_aff_rbbb_le": 0,
        "chf_from_aff_boost": 0,
        "chf_from_aff_inhibit_aff": 0,
    }


def load_chunks_by_split(final_mod: Any) -> dict[str, list[Any]]:
    rows = strict_rows_from_split(load_strict_split())
    return {split: final_mod.build_chunks([row for row in rows if row["split"] == split]) for split in SPLITS}


def source_record_by_case(split_rows: list[dict[str, str]]) -> dict[str, str]:
    return {str(row["strict_case_id"]): row["source_record_id"] for row in split_rows}


def class_record_fold_map(chunks: list[Any], source_by_case: dict[str, str], fold_count: int = 2) -> dict[str, int]:
    by_class: dict[str, list[str]] = {cls: [] for cls in CLASSES}
    for chunk in chunks:
        key = source_by_case.get(str(chunk.case_id), f"{chunk.class_label}:{getattr(chunk, 'record_id', '')}")
        if key not in by_class[chunk.class_label]:
            by_class[chunk.class_label].append(key)
    out: dict[str, int] = {}
    for cls in CLASSES:
        for idx, key in enumerate(sorted(by_class[cls])):
            out[key] = idx % fold_count
    return out


def fold_chunks(chunks: list[Any], source_by_case: dict[str, str], fold_count: int = 2) -> list[list[Any]]:
    fold_map = class_record_fold_map(chunks, source_by_case, fold_count)
    folds: list[list[Any]] = [[] for _ in range(fold_count)]
    for chunk in chunks:
        key = source_by_case.get(str(chunk.case_id), f"{chunk.class_label}:{getattr(chunk, 'record_id', '')}")
        folds[fold_map[key]].append(chunk)
    return folds


def metric_for_subset(final_mod: Any, chunks: list[Any], predictions: dict[str, int]) -> dict[str, Any]:
    return final_mod.metric_for_predictions(chunks, predictions)


def candidate_family(candidate: dict[str, Any]) -> str:
    cid = str(candidate.get("candidate_id", candidate.get("candidate", "candidate")))
    if cid.startswith("neutral"):
        return "baseline"
    if cid.startswith("balanced"):
        return "balanced_rules"
    return cid.split("_", 1)[0]


def candidate_complexity(candidate: dict[str, Any]) -> int:
    ignored = {"candidate_id", "candidate"}
    return sum(1 for key, value in candidate.items() if key not in ignored and value not in (False, None, 0, "", "none", 999999, 99, -99))


def is_selectable_membrane_candidate(candidate: dict[str, Any]) -> bool:
    cid = str(candidate.get("candidate_id", candidate.get("candidate", "")))
    if cid.startswith("neutral"):
        return False
    if str(candidate.get("use_mem", "none")) != "none":
        return True
    if str(candidate.get("base_from", "majority")) == "mem":
        return True
    if int(candidate.get("vote_shift", 0) or 0) != 0:
        return True
    return any(int(candidate.get(field, 0) or 0) != 0 for field in ACTIVE_MEMBRANE_FIELDS)


def prediction_signature(chunks: list[Any], predictions: dict[str, int]) -> str:
    return "".join(str(predictions[chunk.case_id]) for chunk in chunks)


def train_prefilter_score(train_m: dict[str, Any], fold_metrics: list[dict[str, Any]], complexity: int) -> tuple[float, float, float, float, float]:
    bas = [float(metric["balanced_accuracy"]) for metric in fold_metrics]
    macros = [float(metric["macro_f1"]) for metric in fold_metrics]
    mean_ba = sum(bas) / len(bas)
    std_ba = math.sqrt(sum((value - mean_ba) ** 2 for value in bas) / len(bas))
    mean_macro = sum(macros) / len(macros)
    stable = mean_ba - 0.5 * std_ba + 0.25 * mean_macro - 0.0005 * complexity
    return (
        stable,
        float(train_m["balanced_accuracy"]),
        float(train_m["macro_f1"]),
        float(train_m["min_recall"]),
        -float(complexity),
    )


def push_top(heap: list[tuple[Any, int, dict[str, Any]]], key: tuple[Any, ...], row: dict[str, Any], limit: int) -> None:
    item = (key, int(row["trial"]), row)
    if len(heap) < limit:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def candidate_stream(final_mod: Any, families: list[str], include_neutral_baseline: bool = False) -> Iterable[dict[str, Any]]:
    if include_neutral_baseline and "baseline" in families:
        yield neutral_params()
    if "full" in families:
        for candidate in final_mod.candidate_grid():
            if is_selectable_membrane_candidate(candidate):
                yield candidate
    if "balanced" in families:
        for candidate in final_mod.balanced_candidate_grid():
            if is_selectable_membrane_candidate(candidate):
                yield candidate


def write_stage_a_summary(path: Path, rows: list[dict[str, Any]], counts: dict[str, int], split_hash: str) -> None:
    lines = [
        "# Strict Record-wise SNN Final Membrane Huge-grid Stage A",
        "",
        f"- Split hash: `{split_hash}`",
        "- Stage A data: `train only`",
        "- Validation/test used: `false`",
        "- Selectable candidate scope: `SNN membrane candidates only`",
        "- Pure neutral majority baseline selectable: `false`",
        f"- Total candidates evaluated: `{sum(counts.values())}`",
        "",
        "## Candidate Counts",
        "",
        md_table(["family", "count"], sorted(counts.items())),
        "",
        "## Top Train-only Candidates",
        "",
        md_table(
            ["rank", "candidate", "family", "train_bal_acc", "train_macro_f1", "prefilter_score", "complexity"],
            [
                [
                    idx + 1,
                    row["candidate_id"],
                    row["family"],
                    f"{float(row['train_balanced_accuracy']):.6f}",
                    f"{float(row['train_macro_f1']):.6f}",
                    f"{float(row['prefilter_score']):.6f}",
                    row["complexity"],
                ]
                for idx, row in enumerate(rows[:20])
            ],
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def command_search(args: argparse.Namespace) -> None:
    final_mod = load_final_module()
    chunks = load_chunks_by_split(final_mod)
    train = chunks["train"]
    val = chunks["val"]
    split_payload = read_json(split_json_path(args.seed))
    split_rows = load_strict_split()
    source_by_case_all = source_record_by_case(split_rows)
    train_folds = fold_chunks(train, source_by_case_all, fold_count=2)
    record_lists = record_lists_from_split(split_rows)
    split_hash = split_payload["split_hash"]

    write_json(
        FIXED_SNAPSHOT,
        {
            "fixed_snapshot_frontend": "existing active C24/V2 window dump from results/final_membrane_v2_snn",
            "snapshot_search_performed_in_this_flow": False,
            "reason": "user requested final membrane structure/parameter search only",
            "final_membrane_search_scope": "existing SNN final membrane shell; pure neutral majority is report-only and not selectable",
        },
    )
    fixed_snapshot_artifact = artifact_manifest([FIXED_SNAPSHOT])
    frontend_artifacts = frontend_artifact_manifest()
    script_artifacts = search_script_manifest()

    global_heap: list[tuple[Any, int, dict[str, Any]]] = []
    family_heaps: dict[str, list[tuple[Any, int, dict[str, Any]]]] = defaultdict(list)
    counts: Counter[str] = Counter()
    trial = 0
    stage_a_path = OUT / "final_membrane_huge_stage_a_top_train.csv"
    stage_a_path.parent.mkdir(parents=True, exist_ok=True)

    families = [part.strip() for part in args.families.split(",") if part.strip()]
    for candidate in candidate_stream(final_mod, families, include_neutral_baseline=args.include_neutral_baseline):
        trial += 1
        family = candidate_family(candidate)
        counts[family] += 1
        pred, _ = final_mod.apply_candidate(train, candidate)
        train_m = final_mod.metric_for_predictions(train, pred)
        fold_metrics = [metric_for_subset(final_mod, fold, pred) for fold in train_folds]
        complexity = candidate_complexity(candidate)
        key = train_prefilter_score(train_m, fold_metrics, complexity)
        row = {
            "trial": trial,
            "candidate_id": candidate.get("candidate_id", candidate.get("candidate", f"candidate_{trial}")),
            "family": family,
            "complexity": complexity,
            "prefilter_score": key[0],
            "train_accuracy": train_m["accuracy"],
            "train_macro_f1": train_m["macro_f1"],
            "train_balanced_accuracy": train_m["balanced_accuracy"],
            "train_min_recall": train_m["min_recall"],
            "fold0_balanced_accuracy": fold_metrics[0]["balanced_accuracy"],
            "fold1_balanced_accuracy": fold_metrics[1]["balanced_accuracy"],
            "train_signature": prediction_signature(train, pred),
            "params_json": json.dumps(candidate, sort_keys=True, separators=(",", ":")),
        }
        push_top(global_heap, key, row, args.global_top)
        push_top(family_heaps[family], key, row, args.family_top)
        if args.max_candidates and trial >= args.max_candidates:
            break
        if trial % args.progress_every == 0:
            best = max(global_heap)[2]
            print(
                f"stageA {trial} candidates; best={best['candidate_id']} "
                f"score={float(best['prefilter_score']):.6f} trainBA={float(best['train_balanced_accuracy']):.4f}",
                flush=True,
            )

    shortlist_pool: list[dict[str, Any]] = [item[2] for item in global_heap]
    for heap in family_heaps.values():
        shortlist_pool.extend(item[2] for item in heap)
    shortlist_pool.sort(
        key=lambda row: (
            float(row["prefilter_score"]),
            float(row["train_balanced_accuracy"]),
            float(row["train_macro_f1"]),
            float(row["train_min_recall"]),
            -float(row["complexity"]),
        ),
        reverse=True,
    )

    deduped: list[dict[str, Any]] = []
    seen_signatures: set[str] = set()
    seen_params: set[str] = set()
    for row in shortlist_pool:
        sig = str(row["train_signature"])
        params_json = str(row["params_json"])
        if sig in seen_signatures or params_json in seen_params:
            continue
        seen_signatures.add(sig)
        seen_params.add(params_json)
        deduped.append(row)
        if len(deduped) >= args.shortlist:
            break
    if not deduped:
        raise RuntimeError("empty validation shortlist")

    validation_rows: list[dict[str, Any]] = []
    best_val_row: dict[str, Any] | None = None
    best_params: dict[str, Any] | None = None
    tie_epsilon = 1.0 / max(1, len(val))
    for idx, row in enumerate(deduped, 1):
        params = json.loads(str(row["params_json"]))
        val_pred, val_details = final_mod.apply_candidate(val, params)
        val_m = final_mod.metric_for_predictions(val, val_pred)
        val_row = dict(row)
        val_row.update(
            {
                "validation_rank_input": idx,
                "val_accuracy": val_m["accuracy"],
                "val_macro_f1": val_m["macro_f1"],
                "val_balanced_accuracy": val_m["balanced_accuracy"],
                "val_min_recall": val_m["min_recall"],
                "val_recall_range": val_m["recall_range"],
                "val_NSR_recall": val_m["per_class"]["NSR"]["recall"],
                "val_CHF_recall": val_m["per_class"]["CHF"]["recall"],
                "val_ARR_recall": val_m["per_class"]["ARR"]["recall"],
                "val_AFF_recall": val_m["per_class"]["AFF"]["recall"],
            }
        )
        validation_rows.append(val_row)
        if best_val_row is None:
            best_val_row = val_row
            best_params = params
            continue
        best_ba = float(best_val_row["val_balanced_accuracy"])
        cur_ba = float(val_row["val_balanced_accuracy"])
        if cur_ba > best_ba + tie_epsilon:
            best_val_row = val_row
            best_params = params
        elif abs(cur_ba - best_ba) <= tie_epsilon:
            current_key = (
                float(val_row["val_macro_f1"]),
                float(val_row["val_min_recall"]),
                float(val_row["prefilter_score"]),
                -float(val_row["complexity"]),
                str(val_row["candidate_id"]),
            )
            best_key = (
                float(best_val_row["val_macro_f1"]),
                float(best_val_row["val_min_recall"]),
                float(best_val_row["prefilter_score"]),
                -float(best_val_row["complexity"]),
                str(best_val_row["candidate_id"]),
            )
            if current_key > best_key:
                best_val_row = val_row
                best_params = params

    validation_rows.sort(
        key=lambda row: (
            float(row["val_balanced_accuracy"]),
            float(row["val_macro_f1"]),
            float(row["val_min_recall"]),
            float(row["prefilter_score"]),
            -float(row["complexity"]),
        ),
        reverse=True,
    )
    top_train_rows = [item[2] for item in sorted(global_heap, reverse=True)]
    write_csv(stage_a_path, top_train_rows)
    write_csv(OUT / "final_membrane_huge_validation_shortlist.csv", validation_rows)
    assert best_val_row is not None and best_params is not None
    selected_pred, selected_details = final_mod.apply_candidate(val, best_params)
    selected_val_m = final_mod.metric_for_predictions(val, selected_pred)
    selected_train_pred, selected_train_details = final_mod.apply_candidate(train, best_params)
    selected_train_m = final_mod.metric_for_predictions(train, selected_train_pred)

    lock_payload = {
        "selected_before_test_evaluation": True,
        "test_used_for_selection": False,
        "split_hash": split_hash,
        "train_record_list_hash": sha256_json(record_lists["train"]),
        "val_record_list_hash": sha256_json(record_lists["val"]),
        "test_record_list_hash": sha256_json(record_lists["test"]),
        "fixed_snapshot_path": rel_path(FIXED_SNAPSHOT),
        "fixed_snapshot_artifact": fixed_snapshot_artifact,
        "fixed_frontend_artifacts": frontend_artifacts,
        "search_script_artifacts": script_artifacts,
        "chatgpt_55pro_session": args.chatgpt_session,
        "search_protocol": {
            "stage_a": "huge grid evaluated on train only",
            "stage_b": "top train candidates deduped by train prediction signature",
            "stage_c": "shortlist evaluated on validation once",
            "stage_d": "held-out test must be evaluated only after this lock",
            "families": families,
            "selectable_candidate_scope": "SNN membrane candidates only",
            "neutral_majority_baseline_selectable": bool(args.include_neutral_baseline),
            "pure_majority_guard": "candidate must have active membrane evidence path: use_mem, base_from=mem, vote_shift, or nonzero boost/inhibit current",
            "total_candidates_evaluated": trial,
            "shortlist_size": len(deduped),
            "validation_tie_epsilon": tie_epsilon,
            "selection_metric": "validation balanced accuracy with one-chunk tie zone, then macro-F1, min recall, train prefilter score, lower complexity",
        },
        "candidate_counts_by_family": dict(counts),
        "selected_candidate_row": best_val_row,
        "selected_candidate_params_hash": sha256_json(best_params),
        "params": best_params,
        "train_metrics": selected_train_m,
        "val_metrics": selected_val_m,
    }
    write_json(LOCKED_PARAMS, lock_payload)
    write_json(OUT / "final_membrane_huge_search_summary.json", lock_payload)
    write_stage_a_summary(OUT / "final_membrane_huge_stage_a_summary.md", top_train_rows, dict(counts), split_hash)
    write_search_summary_md(OUT / "final_membrane_huge_search_summary.md", lock_payload, validation_rows[:20])
    write_log(
        "search_final_membrane_huge_grid",
        sys.argv,
        [
            FIXED_SNAPSHOT,
            stage_a_path,
            OUT / "final_membrane_huge_validation_shortlist.csv",
            LOCKED_PARAMS,
            OUT / "final_membrane_huge_search_summary.json",
            OUT / "final_membrane_huge_search_summary.md",
        ],
        {"test_used_for_selection": False, "candidate_count": trial, "shortlist_size": len(deduped)},
    )
    print(
        f"selected {best_val_row['candidate_id']} candidates={trial} shortlist={len(deduped)} "
        f"val={selected_val_m['correct']}/{selected_val_m['total']} macro_f1={selected_val_m['macro_f1']:.4f}",
        flush=True,
    )


def write_search_summary_md(path: Path, payload: dict[str, Any], top_val_rows: list[dict[str, Any]]) -> None:
    train = payload["train_metrics"]
    val = payload["val_metrics"]
    rows = [
        ["train", f"{train['correct']}/{train['total']}", pct(train["accuracy"]), pct(train["macro_f1"]), pct(train["balanced_accuracy"])],
        ["validation", f"{val['correct']}/{val['total']}", pct(val["accuracy"]), pct(val["macro_f1"]), pct(val["balanced_accuracy"])],
    ]
    lines = [
        "# Strict Record-wise SNN Final Membrane Huge-grid Search",
        "",
        "- Stage A: train-only huge grid",
        "- Stage B: train-signature deduped shortlist",
        "- Stage C: validation-only final selection",
        "- Test used for selection: `false`",
        "- Selectable candidate scope: `SNN membrane candidates only`",
        "- Pure neutral majority baseline selectable: `false`",
        f"- Candidate count: `{payload['search_protocol']['total_candidates_evaluated']}`",
        f"- Shortlist size: `{payload['search_protocol']['shortlist_size']}`",
        f"- Selected candidate: `{payload['selected_candidate_row']['candidate_id']}`",
        "",
        "## Selected Metrics",
        "",
        md_table(["split", "correct/total", "accuracy", "macro-F1", "balanced accuracy"], rows),
        "",
        "## Validation Top Candidates",
        "",
        md_table(
            ["rank", "candidate", "family", "val_bal_acc", "val_macro_f1", "val_min_recall", "train_prefilter"],
            [
                [
                    idx + 1,
                    row["candidate_id"],
                    row["family"],
                    f"{float(row['val_balanced_accuracy']):.6f}",
                    f"{float(row['val_macro_f1']):.6f}",
                    f"{float(row['val_min_recall']):.6f}",
                    f"{float(row['prefilter_score']):.6f}",
                ]
                for idx, row in enumerate(top_val_rows)
            ],
        ),
        "",
        "## Selected Params",
        "",
        "```json",
        json.dumps(payload["params"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Caveats",
        "",
        "- Validation has 32 chunks, so one validation chunk is 3.125 percentage points.",
        "- AFF has low source-record diversity; AFF validation is a one-source stress check.",
        "- Snapshot front-end is fixed; this search changes only the final membrane decision structure/parameters.",
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def prediction_rows(chunks: list[Any], pred: dict[str, int], details: dict[str, dict[str, Any]], source_by_case: dict[str, str]) -> list[dict[str, Any]]:
    out = []
    for chunk in chunks:
        item = {
            "case_id": chunk.case_id,
            "source_record_id": source_by_case.get(str(chunk.case_id), ""),
            "class_label": chunk.class_label,
            "class_id": chunk.class_id,
            "record_id": chunk.record_id,
            "chunk_id": chunk.chunk_id,
            "chunk_file": chunk.chunk_file,
            "pred_class": pred[chunk.case_id],
            "pred_label": CLASSES[pred[chunk.case_id]],
            "correct": int(pred[chunk.case_id] == chunk.class_id),
        }
        item.update(details[chunk.case_id])
        out.append(item)
    return out


def record_level(rows: list[dict[str, Any]]) -> tuple[list[int], list[int], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["source_record_id"]].append(row)
    true_ids: list[int] = []
    pred_ids: list[int] = []
    out_rows: list[dict[str, Any]] = []
    for record, items in sorted(grouped.items()):
        cls_id = int(items[0]["class_id"])
        counts = [0, 0, 0, 0]
        for item in items:
            counts[int(item["pred_class"])] += 1
        pred = argmax(counts)
        true_ids.append(cls_id)
        pred_ids.append(pred)
        out_rows.append(
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
    return true_ids, pred_ids, out_rows


def command_final_test(args: argparse.Namespace) -> None:
    if not LOCKED_PARAMS.exists():
        raise SystemExit(f"locked params missing: {LOCKED_PARAMS}")
    count_path = FINAL_TEST_OUT / "test_evaluation_count.json"
    locked = read_json(LOCKED_PARAMS)
    split_hash = locked["split_hash"]
    assert_artifact_manifest(locked.get("fixed_snapshot_artifact", []), "fixed snapshot")
    assert_artifact_manifest(locked.get("fixed_frontend_artifacts", []), "fixed frontend")
    params_hash = sha256_json(locked["params"])
    if params_hash != locked.get("selected_candidate_params_hash"):
        raise RuntimeError("locked params hash mismatch")
    eval_script_artifacts = search_script_manifest()
    eval_key_payload = {
        "split_hash": split_hash,
        "train_record_list_hash": locked.get("train_record_list_hash"),
        "val_record_list_hash": locked.get("val_record_list_hash"),
        "test_record_list_hash": locked.get("test_record_list_hash"),
        "fixed_snapshot_artifact": locked.get("fixed_snapshot_artifact", []),
        "fixed_frontend_artifacts": locked.get("fixed_frontend_artifacts", []),
        "params_hash": params_hash,
        "eval_script_artifacts": eval_script_artifacts,
    }
    eval_key_hash = sha256_json(eval_key_payload)
    if count_path.exists():
        count_payload = read_json(count_path)
        if not args.allow_rerun:
            raise SystemExit(f"huge-grid final test already evaluated: {count_path}")
        if count_payload.get("evaluation_key_hash") != eval_key_hash:
            raise SystemExit("refusing --allow-rerun with a different evaluation key")
        eval_count = int(count_payload.get("test_evaluation_count", 0)) + 1
        warning = "explicit --allow-rerun used for the same evaluation key"
    else:
        eval_count = 1
        warning = None

    final_mod = load_final_module()
    chunks = load_chunks_by_split(final_mod)
    test = chunks["test"]
    params = locked["params"]
    pred, details = final_mod.apply_candidate(test, params)
    metric = final_mod.metric_for_predictions(test, pred)
    split_rows = load_strict_split()
    source_by_case = {str(row["strict_case_id"]): row["source_record_id"] for row in split_rows if row["split"] == "test"}
    pred_rows = prediction_rows(test, pred, details, source_by_case)
    rec_true, rec_pred, rec_rows = record_level(pred_rows)
    rec_metric = metric_from_pairs(rec_true, rec_pred)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "test_evaluation_count": eval_count,
        "split_hash": split_hash,
        "test_used_for_selection": False,
        "locked_params_path": str(LOCKED_PARAMS),
        "evaluation_key_hash": eval_key_hash,
        "evaluation_key_payload": eval_key_payload,
        "warning": warning,
        "chunk_level": metric,
        "record_level_majority": rec_metric,
        "test_chunk_count_by_class": dict(Counter(row["class_label"] for row in pred_rows)),
        "test_record_count_by_class": dict(Counter(row["class_label"] for row in rec_rows)),
    }
    FINAL_TEST_OUT.mkdir(parents=True, exist_ok=True)
    write_csv(FINAL_TEST_OUT / "final_membrane_huge_test_predictions.csv", pred_rows)
    write_csv(FINAL_TEST_OUT / "final_membrane_huge_test_record_predictions.csv", rec_rows)
    write_csv(FINAL_TEST_OUT / "final_membrane_huge_test_confusion_matrix.csv", confusion_rows(metric))
    write_json(FINAL_TEST_OUT / "final_membrane_huge_test_metrics.json", payload)
    write_json(
        count_path,
        {
            "test_evaluation_count": eval_count,
            "split_hash": split_hash,
            "evaluation_key_hash": eval_key_hash,
            "timestamp_utc": payload["timestamp_utc"],
            "warning": warning,
        },
    )
    write_final_test_summary(FINAL_TEST_OUT / "final_membrane_huge_test_summary.md", payload)
    write_log(
        "evaluate_final_membrane_huge_grid_test_once",
        sys.argv,
        [
            FINAL_TEST_OUT / "final_membrane_huge_test_predictions.csv",
            FINAL_TEST_OUT / "final_membrane_huge_test_record_predictions.csv",
            FINAL_TEST_OUT / "final_membrane_huge_test_metrics.json",
            FINAL_TEST_OUT / "final_membrane_huge_test_summary.md",
            count_path,
        ],
        {"test_evaluation_count": eval_count, "split_hash": split_hash},
    )
    print(f"huge-grid final-test {metric['correct']}/{metric['total']} macro_f1={metric['macro_f1']:.4f}", flush=True)


def write_final_test_summary(path: Path, payload: dict[str, Any]) -> None:
    chunk = payload["chunk_level"]
    rec = payload["record_level_majority"]
    lines = [
        "# Strict Record-wise SNN Final Membrane Huge-grid Final Test",
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
        md_table(["class", "recall", "precision", "f1", "support"], [[cls, pct(float(chunk["per_class"][cls]["recall"])), pct(float(chunk["per_class"][cls]["precision"])), pct(float(chunk["per_class"][cls]["f1"])), chunk["per_class"][cls]["support"]] for cls in CLASSES]),
    ]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Huge-grid final membrane search on strict record-wise 30-minute split.")
    sub = parser.add_subparsers(required=True)
    search = sub.add_parser("search")
    search.add_argument("--seed", type=int, default=2026)
    search.add_argument("--families", default="full,balanced")
    search.add_argument("--include-neutral-baseline", action="store_true")
    search.add_argument("--max-candidates", type=int, default=0)
    search.add_argument("--global-top", type=int, default=256)
    search.add_argument("--family-top", type=int, default=96)
    search.add_argument("--shortlist", type=int, default=64)
    search.add_argument("--progress-every", type=int, default=50000)
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
