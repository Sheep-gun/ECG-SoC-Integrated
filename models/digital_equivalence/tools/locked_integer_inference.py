#!/usr/bin/env python3
"""Locked integer-equivalent SNN inference used only by the benchmark.

The cycle model was recovered from historical commit ef48850c, reads the
current locked RTL constants, and models the final delayed valid/data staging.
This module does not search or modify parameters.
"""

from __future__ import annotations

import ast
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from snapshot_c24_rtl_exact import SnapshotFrontEnd, s12_from_hex_mem
from search_final_membrane_v2_snn import Chunk, candidate_predict


INTEGRATED_ROOT = Path(__file__).resolve().parents[3]
DIGITAL_ROOT = INTEGRATED_ROOT / "design" / "digital"
BENCH = INTEGRATED_ROOT / "models" / "digital_equivalence"
BASE_PARAMS = BENCH / "reference" / "best_final_membrane_snn_huge_grid_locked.json"
STRUCT_PARAMS = DIGITAL_ROOT / "configs" / "recordwise_resplit_seed20260808" / "best_final_membrane_structural_grid_locked.json"
STRUCT_SOURCE = BENCH / "tools" / "search_final_membrane_structural_grid.py"
CLASSES = ("NSR", "CHF", "ARR", "AFF")


def _load_structural_predictor():
    """Compile only the two pure functions, avoiding historical search imports."""
    tree = ast.parse(STRUCT_SOURCE.read_text(encoding="utf-8"))
    wanted = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in {"argmax4", "predict_structural"}
    ]
    module = ast.Module(body=wanted, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict[str, Any] = {}
    exec(compile(module, str(STRUCT_SOURCE), "exec"), namespace)
    return namespace["predict_structural"]


PREDICT_STRUCTURAL = _load_structural_predictor()


def _window_result(front: SnapshotFrontEnd) -> dict[str, int]:
    qrs_maf_count = front.qrs_maf_count
    morphology = (
        front.dscr_flip_count
        + qrs_maf_count
        + front.qrs_width_abn_count
        + front.qrs_complex_abn_count
        + front.qrs_energy_abn_count
        + front.rbbb_delay_like_count
    )
    abnormal = (
        front.pnn_mismatch_count
        + front.ectopic_pair_count
        + qrs_maf_count
        + front.qrs_width_abn_count
        + front.qrs_complex_abn_count
        + front.qrs_energy_abn_count
        + front.rbbb_delay_like_count
    )
    return {
        "pred_class": int(front.score.pred_class),
        "class_mem_NSR": int(front.score.c24_mem[0]),
        "class_mem_CHF": int(front.score.c24_mem[1]),
        "class_mem_ARR": int(front.score.c24_mem[2]),
        "class_mem_AFF": int(front.score.c24_mem[3]),
        "score_NSR": int(front.score.score_mem[0]),
        "score_CHF": int(front.score.score_mem[1]),
        "score_ARR": int(front.score.score_mem[2]),
        "score_AFF": int(front.score.score_mem[3]),
        "rbbb_qrs_delay_applied": int(front.score.rbbb_qrs_delay_applied),
        "beat_count": front.qrs_count,
        "pnn_match_count": front.pnn_match_count,
        "pnn_mismatch_count": front.pnn_mismatch_count,
        "dscr_flip_count": front.dscr_flip_count,
        "dscr_slope_count": front.dscr_slope_count,
        "ram_code_sum": front.ram_code_sum,
        "ram_code_count": front.ram_code_count,
        "rdm_valid_count": front.rdm_valid_count,
        "rdm_code_sum": front.rdm_code_sum,
        "ectopic_pair_count": front.ectopic_pair_count,
        "qrs_maf_count": qrs_maf_count,
        "qrs_width_abn_count": front.qrs_width_abn_count,
        "qrs_complex_abn_count": front.qrs_complex_abn_count,
        "qrs_energy_abn_count": front.qrs_energy_abn_count,
        "rbbb_delay_like_count": front.rbbb_delay_like_count,
        "rbbb_delay_applied_count": front.rbbb_delay_applied_count,
        "pre_qrs_bump_count": front.pre_qrs_bump_count,
        "abnormal_evidence_count": abnormal,
        "rhythm_irregular_evidence_count": (
            front.pnn_mismatch_count + front.rdm_code_sum + front.ectopic_pair_count
        ),
        "morphology_evidence_count": morphology,
    }


def run_snapshot(
    samples: np.ndarray,
    *,
    inter_sample_idle_cycles: int = 0,
    post_done_ticks: int = 37,
) -> dict[str, int]:
    """Run one locked 60-second snapshot without file I/O."""
    if len(samples) != 60_000:
        raise ValueError(f"snapshot must contain 60000 samples, got {len(samples)}")
    front = SnapshotFrontEnd()
    front.reset()
    front.tick(sample_valid=0, rhythm_tick=0, segment_start=1, adc_data=0)
    for raw in samples:
        sample = int(raw)
        front.tick(sample_valid=1, rhythm_tick=1, segment_start=0, adc_data=sample)
        for _ in range(inter_sample_idle_cycles):
            # qrs_sample_valid is delayed by one cycle in the RTL and is paired
            # with a held sample-data pipeline register.  Keep the last
            # accepted sample stable here so the Python clock model observes
            # the same valid/data pair during the first idle cycle.
            front.tick(sample_valid=0, rhythm_tick=0, segment_start=0, adc_data=sample)
    last_sample = int(samples[-1])
    front.tick(sample_valid=0, rhythm_tick=0, segment_start=0, segment_done=1, adc_data=last_sample)
    for _ in range(post_done_ticks):
        front.tick(sample_valid=0, rhythm_tick=0, segment_start=0, segment_done=0, adc_data=last_sample)
    return _window_result(front)


def infer_loaded(
    samples: np.ndarray,
    *,
    inter_sample_idle_cycles: int = 0,
    post_done_ticks: int = 37,
) -> dict[str, Any]:
    """Process one already-loaded 1,800,000-sample signed-12-bit stream."""
    if samples.dtype.kind != "i":
        raise TypeError(f"samples must be a signed integer array, got {samples.dtype}")
    if len(samples) != 1_800_000:
        raise ValueError(f"case must contain 1800000 samples, got {len(samples)}")
    if int(samples.min()) < -2048 or int(samples.max()) > 2047:
        raise ValueError("samples violate signed 12-bit input contract")

    windows = [
        run_snapshot(
            samples[offset : offset + 60_000],
            inter_sample_idle_cycles=inter_sample_idle_cycles,
            post_done_ticks=post_done_ticks,
        )
        for offset in range(0, 1_800_000, 60_000)
    ]
    counts = [0, 0, 0, 0]
    mem_sum = [0, 0, 0, 0]
    mem_max = [-(1 << 63)] * 4
    feature_keys = [
        "beat_count",
        "pnn_match_count",
        "pnn_mismatch_count",
        "dscr_flip_count",
        "dscr_slope_count",
        "ram_code_sum",
        "ram_code_count",
        "rdm_valid_count",
        "rdm_code_sum",
        "ectopic_pair_count",
        "qrs_maf_count",
        "qrs_width_abn_count",
        "qrs_complex_abn_count",
        "qrs_energy_abn_count",
        "rbbb_delay_like_count",
        "rbbb_delay_applied_count",
        "pre_qrs_bump_count",
        "abnormal_evidence_count",
        "rhythm_irregular_evidence_count",
        "morphology_evidence_count",
    ]
    feature_sum = {key: 0 for key in feature_keys}
    for row in windows:
        counts[row["pred_class"]] += 1
        for idx, cls in enumerate(CLASSES):
            value = row[f"class_mem_{cls}"]
            mem_sum[idx] += value
            mem_max[idx] = max(mem_max[idx], value)
        for key in feature_keys:
            feature_sum[key] += row[key]

    chunk = Chunk(
        case_id="benchmark",
        split="test",
        class_id=-1,
        class_label="",
        record_id="",
        chunk_id="",
        chunk_file="",
        pred_count=counts,
        mem_sum=mem_sum,
        mem_max=mem_max,
        feature_sum=feature_sum,
    )
    base_params = json.loads(BASE_PARAMS.read_text(encoding="utf-8-sig"))["params"]
    _, base_mem, base_flags = candidate_predict(chunk, base_params)
    struct_params = json.loads(STRUCT_PARAMS.read_text(encoding="utf-8-sig"))["params"]
    row = {
        "counts": counts,
        "base_mem": base_mem,
        "qrs": feature_sum["qrs_maf_count"],
        "ect": feature_sum["ectopic_pair_count"],
        "morph": feature_sum["morphology_evidence_count"],
        "rhythm": feature_sum["rhythm_irregular_evidence_count"],
        "pre": feature_sum["pre_qrs_bump_count"],
        "abn": feature_sum["abnormal_evidence_count"],
        "rbbb": feature_sum["rbbb_delay_like_count"],
        "beat": feature_sum["beat_count"],
        "ram": feature_sum["ram_code_sum"],
        "rdm_valid": feature_sum["rdm_valid_count"],
        "rdm_sum": feature_sum["rdm_code_sum"],
    }
    pred, final_mem, struct_flags = PREDICT_STRUCTURAL(row, struct_params)
    return {
        "sample_count": len(samples),
        "snapshot_count": len(windows),
        "final_pred": int(pred),
        "final_mem_NSR": int(final_mem[0]),
        "final_mem_CHF": int(final_mem[1]),
        "final_mem_ARR": int(final_mem[2]),
        "final_mem_AFF": int(final_mem[3]),
        "snapshot_pred_counts": counts,
        "base_flags": base_flags,
        "struct_flags": struct_flags,
    }


def infer_file(path: Path, **kwargs: Any) -> dict[str, Any]:
    return infer_loaded(s12_from_hex_mem(path), **kwargs)
