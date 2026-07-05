#!/usr/bin/env python3
"""Export the locked strict record-wise Final Membrane parameters for RTL.

The source of truth is the locked structural-grid candidate under
configs/recordwise_resplit_seed20260808.  This script intentionally does not
run any search or evaluation; it only converts the locked JSON artifacts into
Verilog-friendly constants and a short submission report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recordwise_common import REPO, read_json, sha256_json, write_json


RUN_ID = "recordwise_resplit_seed20260808"
SPLIT_SEED = 20260808

CONFIG_DIR = REPO / "configs" / RUN_ID
LOCKED_JSON = CONFIG_DIR / "best_final_membrane_structural_grid_locked.json"
BASE_JSON = CONFIG_DIR / "best_final_membrane_snn_huge_grid_locked.json"

RTL_DIR = REPO / "rtl"
RTL_INCLUDE = RTL_DIR / "strict_recordwise_locked_params.vh"
RTL_GENERATED_DIR = RTL_DIR / "generated"
RTL_PACKAGE = RTL_GENERATED_DIR / "strict_recordwise_locked_params_pkg.sv"

REPORT_DIR = REPO / "reports" / "final_submission"
SUMMARY_MD = REPORT_DIR / "locked_params_export_summary.md"
SUMMARY_JSON = REPORT_DIR / "locked_params_export_summary.json"


STRUCT_PARAM_MAP = [
    ("aff_cnt", "STRICT_RW_FINAL_AFF_CNT"),
    ("aff_chf_cnt", "STRICT_RW_FINAL_AFF_CHF_CNT"),
    ("aff_morph_le", "STRICT_RW_FINAL_AFF_MORPH_LE"),
    ("aff_rhythm_ge", "STRICT_RW_FINAL_AFF_RHYTHM_GE"),
    ("aff_qrs_le", "STRICT_RW_FINAL_AFF_QRS_LE"),
    ("nsr_cnt", "STRICT_RW_FINAL_NSR_CNT"),
    ("nsr_chf_cnt", "STRICT_RW_FINAL_NSR_CHF_CNT"),
    ("nsr_morph_le", "STRICT_RW_FINAL_NSR_MORPH_LE"),
    ("nsr_abn_le", "STRICT_RW_FINAL_NSR_ABN_LE"),
    ("nsr_qrs_le", "STRICT_RW_FINAL_NSR_QRS_LE"),
    ("nsr_ect_le", "STRICT_RW_FINAL_NSR_ECT_LE"),
    ("arr_nsr_nsr_cnt", "STRICT_RW_FINAL_ARR_NSR_NSR_CNT"),
    ("arr_nsr_morph_ge", "STRICT_RW_FINAL_ARR_NSR_MORPH_GE"),
    ("arr_nsr_pre_ge", "STRICT_RW_FINAL_ARR_NSR_PRE_GE"),
    ("arr_nsr_arr_cnt", "STRICT_RW_FINAL_ARR_NSR_ARR_CNT"),
    ("arr_nsr_qrs_high_le", "STRICT_RW_FINAL_ARR_NSR_QRS_HIGH_LE"),
    ("arr_nsr_rbbb_high_le", "STRICT_RW_FINAL_ARR_NSR_RBBB_HIGH_LE"),
    ("arr_nsr_arr_low_le", "STRICT_RW_FINAL_ARR_NSR_ARR_LOW_LE"),
    ("arr_nsr_qrs_low_le", "STRICT_RW_FINAL_ARR_NSR_QRS_LOW_LE"),
    ("arr_nsr_ect_low_le", "STRICT_RW_FINAL_ARR_NSR_ECT_LOW_LE"),
    ("arr_nsr_rhythm_low_le", "STRICT_RW_FINAL_ARR_NSR_RHYTHM_LOW_LE"),
    ("arr_aff_aff_cnt", "STRICT_RW_FINAL_ARR_AFF_AFF_CNT"),
    ("arr_aff_arr_cnt", "STRICT_RW_FINAL_ARR_AFF_ARR_CNT"),
    ("arr_aff_morph_ge", "STRICT_RW_FINAL_ARR_AFF_MORPH_GE"),
    ("arr_aff_ect_ge", "STRICT_RW_FINAL_ARR_AFF_ECT_GE"),
    ("arr_aff_qrs_le", "STRICT_RW_FINAL_ARR_AFF_QRS_LE"),
    ("aff_boost", "STRICT_RW_FINAL_AFF_BOOST"),
    ("aff_inh_chf", "STRICT_RW_FINAL_AFF_INH_CHF"),
    ("aff_inh_arr", "STRICT_RW_FINAL_AFF_INH_ARR"),
    ("nsr_boost", "STRICT_RW_FINAL_NSR_BOOST"),
    ("nsr_inh_chf", "STRICT_RW_FINAL_NSR_INH_CHF"),
    ("nsr_inh_arr", "STRICT_RW_FINAL_NSR_INH_ARR"),
    ("arr_nsr_boost", "STRICT_RW_FINAL_ARR_NSR_BOOST"),
    ("arr_nsr_inh_nsr", "STRICT_RW_FINAL_ARR_NSR_INH_NSR"),
    ("arr_nsr_inh_chf", "STRICT_RW_FINAL_ARR_NSR_INH_CHF"),
    ("arr_nsr_inh_aff", "STRICT_RW_FINAL_ARR_NSR_INH_AFF"),
    ("arr_aff_boost", "STRICT_RW_FINAL_ARR_AFF_BOOST"),
    ("arr_aff_inh_aff", "STRICT_RW_FINAL_ARR_AFF_INH_AFF"),
]


BASE_PARAM_MAP = [
    ("aff_low_enable", "STRICT_RW_BASE_AFF_LOW_ENABLE", 0),
    ("aff_low_abn_le", "STRICT_RW_BASE_AFF_LOW_ABN_LE", 0),
    ("aff_low_morph_le", "STRICT_RW_BASE_AFF_LOW_MORPH_LE", 0),
    ("aff_low_rbbb_le", "STRICT_RW_BASE_AFF_LOW_RBBB_LE", 0),
    ("aff_low_rdm_ge", "STRICT_RW_BASE_AFF_LOW_RDM_GE", 0),
    ("aff_low_chf_count_ge", "STRICT_RW_BASE_AFF_LOW_CHF_COUNT_GE", 99),
    ("aff_low_boost", "STRICT_RW_BASE_AFF_LOW_BOOST", 0),
    ("aff_low_inhibit_chf", "STRICT_RW_BASE_AFF_LOW_INHIBIT_CHF", 0),
    ("nsr_from_chf_nsr_count_ge", "STRICT_RW_BASE_NSR_FROM_CHF_NSR_COUNT_GE", 99),
    ("nsr_from_chf_abn_le", "STRICT_RW_BASE_NSR_FROM_CHF_ABN_LE", 0),
    ("nsr_from_chf_qrs_le", "STRICT_RW_BASE_NSR_FROM_CHF_QRS_LE", 0),
    ("nsr_from_chf_rbbb_le", "STRICT_RW_BASE_NSR_FROM_CHF_RBBB_LE", 0),
    ("nsr_from_chf_morph_le", "STRICT_RW_BASE_NSR_FROM_CHF_MORPH_LE", 0),
    ("nsr_from_chf_boost", "STRICT_RW_BASE_NSR_FROM_CHF_BOOST", 0),
    ("nsr_from_chf_inhibit_chf", "STRICT_RW_BASE_NSR_FROM_CHF_INHIBIT_CHF", 0),
    ("chf_from_aff_chf_count_ge", "STRICT_RW_BASE_CHF_FROM_AFF_CHF_COUNT_GE", 99),
    ("chf_from_aff_morph_le", "STRICT_RW_BASE_CHF_FROM_AFF_MORPH_LE", 0),
    ("chf_from_aff_qrs_le", "STRICT_RW_BASE_CHF_FROM_AFF_QRS_LE", 0),
    ("chf_from_aff_rbbb_le", "STRICT_RW_BASE_CHF_FROM_AFF_RBBB_LE", 0),
    ("chf_from_aff_boost", "STRICT_RW_BASE_CHF_FROM_AFF_BOOST", 0),
    ("chf_from_aff_inhibit_aff", "STRICT_RW_BASE_CHF_FROM_AFF_INHIBIT_AFF", 0),
    ("strong_nsr_count_ge", "STRICT_RW_BASE_STRONG_NSR_COUNT_GE", 99),
    ("strong_nsr_margin_ge", "STRICT_RW_BASE_STRONG_NSR_MARGIN_GE", 99),
    ("strong_nsr_morph_le", "STRICT_RW_BASE_STRONG_NSR_MORPH_LE", 0),
    ("strong_nsr_qrs_le", "STRICT_RW_BASE_STRONG_NSR_QRS_LE", 0),
    ("strong_chf_count_ge", "STRICT_RW_BASE_STRONG_CHF_COUNT_GE", 99),
    ("strong_chf_margin_ge", "STRICT_RW_BASE_STRONG_CHF_MARGIN_GE", 99),
    ("aff_block_arr_count_ge", "STRICT_RW_BASE_AFF_BLOCK_ARR_COUNT_GE", 99),
    ("aff_count_ge", "STRICT_RW_BASE_AFF_COUNT_GE", 99),
    ("aff_chf_margin_le", "STRICT_RW_BASE_AFF_CHF_MARGIN_LE", -99),
    ("aff_rhythm_ge", "STRICT_RW_BASE_AFF_RHYTHM_GE", 999999),
    ("aff_ecp_ge", "STRICT_RW_BASE_AFF_ECP_GE", 999999),
    ("aff_ecp_le", "STRICT_RW_BASE_AFF_ECP_LE", 999999),
    ("aff_boost", "STRICT_RW_BASE_AFF_BOOST", 0),
    ("aff_inhibit_chf", "STRICT_RW_BASE_AFF_INHIBIT_CHF", 0),
    ("aff_inhibit_arr", "STRICT_RW_BASE_AFF_INHIBIT_ARR", 0),
    ("arr_count_ge", "STRICT_RW_BASE_ARR_COUNT_GE", 99),
    ("arr_aff_count_le", "STRICT_RW_BASE_ARR_AFF_COUNT_LE", 99),
    ("arr_nsr_margin_le", "STRICT_RW_BASE_ARR_NSR_MARGIN_LE", 99),
    ("arr_morph_ge", "STRICT_RW_BASE_ARR_MORPH_GE", 999999),
    ("arr_qrs_ge", "STRICT_RW_BASE_ARR_QRS_GE", 999999),
    ("arr_rbbb_ge", "STRICT_RW_BASE_ARR_RBBB_GE", 999999),
    ("arr_pre_ge", "STRICT_RW_BASE_ARR_PRE_GE", 999999),
    ("arr_boost", "STRICT_RW_BASE_ARR_BOOST", 0),
    ("arr_inhibit_nsr", "STRICT_RW_BASE_ARR_INHIBIT_NSR", 0),
    ("arr_inhibit_chf", "STRICT_RW_BASE_ARR_INHIBIT_CHF", 0),
    ("arr_inhibit_aff", "STRICT_RW_BASE_ARR_INHIBIT_AFF", 0),
    ("aff_rescue_enable", "STRICT_RW_BASE_AFF_RESCUE_ENABLE", 0),
    ("aff_rescue_source_chf", "STRICT_RW_BASE_AFF_RESCUE_SOURCE_CHF", 0),
    ("aff_rescue_source_arr", "STRICT_RW_BASE_AFF_RESCUE_SOURCE_ARR", 0),
    ("aff_rescue_count_ge", "STRICT_RW_BASE_AFF_RESCUE_COUNT_GE", 99),
    ("aff_rescue_chf_margin_le", "STRICT_RW_BASE_AFF_RESCUE_CHF_MARGIN_LE", -99),
    ("aff_rescue_rhythm_ge", "STRICT_RW_BASE_AFF_RESCUE_RHYTHM_GE", 999999),
    ("aff_rescue_ect_ge", "STRICT_RW_BASE_AFF_RESCUE_ECT_GE", 999999),
    ("aff_rescue_arr_count_lt", "STRICT_RW_BASE_AFF_RESCUE_ARR_COUNT_LT", 0),
    ("aff_rescue_boost", "STRICT_RW_BASE_AFF_RESCUE_BOOST", 0),
    ("aff_rescue_inhibit_chf", "STRICT_RW_BASE_AFF_RESCUE_INHIBIT_CHF", 0),
    ("aff_rescue_inhibit_arr", "STRICT_RW_BASE_AFF_RESCUE_INHIBIT_ARR", 0),
    ("arr_low_enable", "STRICT_RW_BASE_ARR_LOW_ENABLE", 1),
    ("arr_low_count_ge", "STRICT_RW_BASE_ARR_LOW_COUNT_GE", 99),
    ("arr_low_aff_count_le", "STRICT_RW_BASE_ARR_LOW_AFF_COUNT_LE", 99),
    ("arr_low_pre_ge", "STRICT_RW_BASE_ARR_LOW_PRE_GE", 999999),
    ("arr_low_qrs_ge", "STRICT_RW_BASE_ARR_LOW_QRS_GE", 999999),
    ("arr_low_rbbb_ge", "STRICT_RW_BASE_ARR_LOW_RBBB_GE", 999999),
    ("arr_low_morph_ge", "STRICT_RW_BASE_ARR_LOW_MORPH_GE", 999999),
    ("arr_low_abn_ge", "STRICT_RW_BASE_ARR_LOW_ABN_GE", 999999),
    ("arr_low_boost", "STRICT_RW_BASE_ARR_LOW_BOOST", 0),
    ("arr_low_inhibit_nsr", "STRICT_RW_BASE_ARR_LOW_INHIBIT_NSR", 0),
    ("arr_low_inhibit_chf", "STRICT_RW_BASE_ARR_LOW_INHIBIT_CHF", 0),
    ("arr_low_inhibit_aff", "STRICT_RW_BASE_ARR_LOW_INHIBIT_AFF", 0),
]


SILENT_AFF_CONSTANTS = [
    ("STRICT_RW_SILENT_AFF_CHF_CNT_GE", 29),
    ("STRICT_RW_SILENT_AFF_NSR_CNT_LE", 1),
    ("STRICT_RW_SILENT_AFF_ARR_CNT_EQ", 0),
    ("STRICT_RW_SILENT_AFF_AFF_CNT_EQ", 0),
    ("STRICT_RW_SILENT_AFF_BEAT_LE", 10),
    ("STRICT_RW_SILENT_AFF_MORPH_LE", 8),
    ("STRICT_RW_SILENT_AFF_RHYTHM_LE", 20),
    ("STRICT_RW_SILENT_AFF_ABN_LE", 10),
    ("STRICT_RW_SILENT_AFF_QRS_LE", 3),
    ("STRICT_RW_SILENT_AFF_ECT_EQ", 0),
    ("STRICT_RW_SILENT_AFF_RAM_EQ", 0),
    ("STRICT_RW_SILENT_AFF_BOOST", 120),
    ("STRICT_RW_SILENT_AFF_INH_CHF", 120),
]


def sv_localparam(name: str, value: int) -> str:
    return f"localparam integer {name} = {int(value)};"


def collect_params(locked: dict[str, Any], base: dict[str, Any]) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    final_params = locked.get("params", {})
    base_params = base.get("params", {})

    final_items: list[tuple[str, int]] = []
    for json_key, sv_name in STRUCT_PARAM_MAP:
        if json_key not in final_params:
            raise KeyError(f"locked structural params missing key: {json_key}")
        final_items.append((sv_name, int(final_params[json_key])))

    base_items: list[tuple[str, int]] = []
    for json_key, sv_name, default in BASE_PARAM_MAP:
        base_items.append((sv_name, int(base_params.get(json_key, default))))

    for sv_name, value in SILENT_AFF_CONSTANTS:
        final_items.append((sv_name, int(value)))

    return final_items, base_items


def build_param_lines(
    locked: dict[str, Any],
    base: dict[str, Any],
    final_items: list[tuple[str, int]],
    base_items: list[tuple[str, int]],
) -> list[str]:
    locked_params_hash = sha256_json(locked.get("params", {}))
    base_params_hash = sha256_json(base.get("params", {}))
    locked_candidate = locked.get("selected_candidate_id") or locked.get("params", {}).get("candidate_id")
    base_candidate = base.get("selected_candidate_id") or base.get("params", {}).get("candidate_id")
    lines = [
        "// Auto-generated by tools/recordwise/export_params_for_rtl.py",
        "// Source: configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json",
        f"// locked_candidate: {locked_candidate}",
        f"// locked_params_hash: {locked_params_hash}",
        f"// base_candidate: {base_candidate}",
        f"// base_params_hash: {base_params_hash}",
        f"// split_seed: {SPLIT_SEED}",
        sv_localparam("STRICT_RW_SPLIT_SEED", SPLIT_SEED),
        sv_localparam("STRICT_RW_CLASS_NSR", 0),
        sv_localparam("STRICT_RW_CLASS_CHF", 1),
        sv_localparam("STRICT_RW_CLASS_ARR", 2),
        sv_localparam("STRICT_RW_CLASS_AFF", 3),
        "",
        "// Base SNN Final Membrane candidate: balanced_0202881",
    ]
    lines.extend(sv_localparam(name, value) for name, value in base_items)
    lines.extend(
        [
            "",
            "// Structural-grid overlay candidate: structural_guarded_silent_aff_1008710",
        ]
    )
    lines.extend(sv_localparam(name, value) for name, value in final_items)
    return lines


def write_outputs(locked: dict[str, Any], base: dict[str, Any], dry_run: bool = False) -> None:
    final_items, base_items = collect_params(locked, base)
    param_lines = build_param_lines(locked, base, final_items, base_items)
    include_text = "\n".join(
        [
            "`ifndef STRICT_RECORDWISE_LOCKED_PARAMS_VH",
            "`define STRICT_RECORDWISE_LOCKED_PARAMS_VH",
            *param_lines,
            "`endif",
            "",
        ]
    )
    package_text = "\n".join(
        [
            "// Auto-generated by tools/recordwise/export_params_for_rtl.py",
            "package strict_recordwise_locked_params_pkg;",
            *["  " + line if line else "" for line in param_lines],
            "endpackage",
            "",
        ]
    )

    locked_params_hash = sha256_json(locked.get("params", {}))
    base_params_hash = sha256_json(base.get("params", {}))
    summary = {
        "run_id": RUN_ID,
        "split_seed": SPLIT_SEED,
        "locked_candidate": locked.get("selected_candidate_id") or locked.get("params", {}).get("candidate_id"),
        "locked_family": locked.get("params", {}).get("family"),
        "locked_params_hash": locked_params_hash,
        "base_candidate": base.get("selected_candidate_id") or base.get("params", {}).get("candidate_id"),
        "base_params_hash": base_params_hash,
        "rtl_include": str(RTL_INCLUDE.relative_to(REPO)),
        "rtl_generated_package": str(RTL_PACKAGE.relative_to(REPO)),
        "python_source_of_truth": str(LOCKED_JSON.relative_to(REPO)),
        "rtl_consumes_include": True,
        "interface_changed": False,
    }

    md = "\n".join(
        [
            "# Locked Final Membrane Parameter Export Summary",
            "",
            "| 항목 | 값 |",
            "|---|---|",
            f"| run_id | `{RUN_ID}` |",
            f"| split_seed | `{SPLIT_SEED}` |",
            f"| locked_candidate | `{summary['locked_candidate']}` |",
            f"| locked_family | `{summary['locked_family']}` |",
            f"| locked_params_hash | `{locked_params_hash}` |",
            f"| base_candidate | `{summary['base_candidate']}` |",
            f"| base_params_hash | `{base_params_hash}` |",
            f"| RTL include | `{summary['rtl_include']}` |",
            f"| generated SV package | `{summary['rtl_generated_package']}` |",
            "| RTL interface changed | `false` |",
            "",
            "## 적용 범위",
            "",
            "- `best_final_membrane_structural_grid_locked.json`을 source of truth로 사용한다.",
            "- RTL은 `rtl/strict_recordwise_locked_params.vh`를 include하여 같은 정수 파라미터를 사용한다.",
            "- Python 재검증은 JSON을 직접 읽고, RTL은 생성된 include를 사용한다.",
            "- top-level port 및 AXI register map은 바뀌지 않는다.",
            "",
        ]
    )

    if dry_run:
        print(include_text)
        return

    RTL_GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    RTL_INCLUDE.write_text(include_text, encoding="utf-8", newline="\n")
    RTL_PACKAGE.write_text(package_text, encoding="utf-8", newline="\n")
    write_json(SUMMARY_JSON, summary)
    SUMMARY_MD.write_text(md, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print include text without writing files")
    args = parser.parse_args()

    locked = read_json(LOCKED_JSON)
    base = read_json(BASE_JSON)

    candidate = locked.get("selected_candidate_id") or locked.get("params", {}).get("candidate_id")
    if candidate != "structural_guarded_silent_aff_1008710":
        raise SystemExit(f"unexpected locked candidate: {candidate}")
    base_candidate = base.get("selected_candidate_id") or base.get("params", {}).get("candidate_id")
    if base_candidate != "balanced_0202881":
        raise SystemExit(f"unexpected base candidate: {base_candidate}")

    write_outputs(locked, base, dry_run=args.dry_run)
    if not args.dry_run:
        print(json.dumps(read_json(SUMMARY_JSON), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
