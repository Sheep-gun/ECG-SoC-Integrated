#!/usr/bin/env python3
"""Run a strict record-wise XSim check for the locked Final Membrane RTL.

This runner simulates final_membrane_layer directly with per-snapshot evidence
rows, then compares RTL final_pred/final_mem against the locked Python golden.
It verifies the locked Final Membrane layer without relabeling older full-top
XSim or board results.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
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
    REPO,
    load_final_module,
    load_strict_split,
    md_table,
    pct,
    strict_rows_from_split,
    write_csv,
    write_json,
    write_log,
)
from search_final_membrane_huge_grid import source_record_by_case  # noqa: E402
from search_final_membrane_structural_grid import compact_chunk_rows, evaluate, load_base_context  # noqa: E402


FINAL_SUBMISSION = REPO / "reports" / "final_submission"
WORK = FINAL_SUBMISSION / "xsim_locked_model_work"
SUMMARY_MD = FINAL_SUBMISSION / "xsim_locked_model_summary.md"
MISMATCH_CSV = FINAL_SUBMISSION / "xsim_locked_model_mismatch.csv"
PRED_CSV = FINAL_SUBMISSION / "xsim_locked_model_predictions.csv"
SUMMARY_JSON = FINAL_SUBMISSION / "xsim_locked_model_summary.json"

XVLOG = Path(r"C:\Xilinx\Vivado\2020.2\bin\xvlog.bat")
XELAB = Path(r"C:\Xilinx\Vivado\2020.2\bin\xelab.bat")
XSIM = Path(r"C:\Xilinx\Vivado\2020.2\bin\xsim.bat")


FEATURE_FIELDS = [
    "beat_count",
    "pnn_mismatch_count",
    "ectopic_pair_count",
    "rdm_ge50_count",
    "rdm_ge100_count",
    "qrs_maf_count",
    "qrs_width_abn_count",
    "qrs_energy_abn_count",
    "rbbb_delay_like_count",
    "rbbb_delay_applied_count",
    "pre_qrs_bump_count",
    "dscr_flip_count",
    "dscr_slope_count",
    "abnormal_evidence_count",
    "rhythm_irregular_evidence_count",
    "morphology_evidence_count",
    "pnn_decision_count",
    "rdm_valid_count",
    "rdm_code_sum",
    "ram_code_sum",
    "ram_code_count",
]


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def i(row: dict[str, Any], key: str) -> int:
    value = row.get(key, 0)
    if value in ("", None):
        return 0
    return int(float(value))


def run(cmd: list[str], cwd: Path, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8", newline="\n")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\nsee {log_path}")


def write_not_run(reason: str) -> None:
    FINAL_SUBMISSION.mkdir(parents=True, exist_ok=True)
    write_csv(MISMATCH_CSV, [{"status": "not_run", "reason": reason}])
    write_csv(PRED_CSV, [{"status": "not_run", "reason": reason}])
    write_json(SUMMARY_JSON, {"status": "not_run", "reason": reason})
    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# XSim Locked Model Summary",
                "",
                "- Status: `not_run`",
                f"- Reason: {reason}",
                "- No XSim/Vivado result is claimed for the locked model in this report.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def select_cases(split: str, max_cases: int | None) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    final_mod = load_final_module()
    chunks, base, _base_lock = load_base_context(final_mod, [split])
    compact = compact_chunk_rows(chunks, base)
    locked = (REPO / "configs" / "recordwise_resplit_seed20260808" / "best_final_membrane_structural_grid_locked.json")
    params = __import__("json").loads(locked.read_text(encoding="utf-8"))["params"]
    metric, predictions, details = evaluate(compact[split], chunks[split], final_mod, params)

    expected: dict[str, dict[str, Any]] = {}
    for row in compact[split]:
        case_id = str(row["case_id"])
        detail = details[case_id]
        expected[case_id] = {
            "case_id": case_id,
            "class_id": int(row["class_id"]),
            "class_label": row["class_label"],
            "record_id": row["record_id"],
            "chunk_id": row["chunk_id"],
            "chunk_file": row["chunk_file"],
            "python_pred_class": int(predictions[case_id]),
            "python_final_mem_NSR": int(detail["final_mem_NSR"]),
            "python_final_mem_CHF": int(detail["final_mem_CHF"]),
            "python_final_mem_ARR": int(detail["final_mem_ARR"]),
            "python_final_mem_AFF": int(detail["final_mem_AFF"]),
            "python_correct": int(predictions[case_id] == int(row["class_id"])),
        }

    split_rows = load_strict_split()
    window_rows = strict_rows_from_split(split_rows, target_splits=[split])
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in window_rows:
        by_case[str(row["case_id"])].append(row)
    for rows in by_case.values():
        rows.sort(key=lambda item: i(item, "snapshot_id"))

    selected = sorted(expected.values(), key=lambda item: int(item["case_id"]))
    if max_cases is not None:
        selected = selected[:max_cases]
    selected_ids = {row["case_id"] for row in selected}
    selected_rows = {case_id: by_case[case_id] for case_id in selected_ids}
    return selected, expected, selected_rows


def verilog_value(value: int) -> str:
    if value < 0:
        return f"-32'sd{abs(value)}"
    return f"32'd{value}"


def write_tb(selected: list[dict[str, Any]], selected_rows: dict[str, list[dict[str, Any]]]) -> Path:
    tb = WORK / "tb_locked_final_membrane.v"
    lines = [
        "`timescale 1ns / 1ps",
        "module tb_locked_final_membrane;",
        "  reg clk = 1'b0;",
        "  reg rst = 1'b1;",
        "  reg clear = 1'b0;",
        "  reg snapshot_done = 1'b0;",
        "  reg chunk_done = 1'b0;",
        "  reg pred_valid = 1'b0;",
        "  reg [1:0] pred_class = 2'd0;",
        "  reg signed [63:0] class_mem_nsr = 64'sd0;",
        "  reg signed [63:0] class_mem_chf = 64'sd0;",
        "  reg signed [63:0] class_mem_arr = 64'sd0;",
        "  reg signed [63:0] class_mem_aff = 64'sd0;",
    ]
    for field in FEATURE_FIELDS:
        lines.append(f"  reg [31:0] {field} = 32'd0;")
    lines.extend(
        [
            "  wire final_valid;",
            "  wire [1:0] final_pred_class;",
            "  wire signed [31:0] final_mem_nsr;",
            "  wire signed [31:0] final_mem_chf;",
            "  wire signed [31:0] final_mem_arr;",
            "  wire signed [31:0] final_mem_aff;",
            "",
            "  always #5 clk = ~clk;",
            "",
            "  final_membrane_layer dut (",
            "    .clk(clk), .rst(rst), .clear(clear), .snapshot_done(snapshot_done), .chunk_done(chunk_done),",
            "    .pred_valid(pred_valid), .pred_class(pred_class),",
            "    .class_mem_nsr(class_mem_nsr), .class_mem_chf(class_mem_chf),",
            "    .class_mem_arr(class_mem_arr), .class_mem_aff(class_mem_aff),",
        ]
    )
    port_lines = [f"    .{field}({field})" for field in FEATURE_FIELDS]
    lines.extend([line + "," for line in port_lines])
    lines.extend(
        [
            "    .final_valid(final_valid), .final_pred_class(final_pred_class),",
            "    .final_mem_nsr(final_mem_nsr), .final_mem_chf(final_mem_chf),",
            "    .final_mem_arr(final_mem_arr), .final_mem_aff(final_mem_aff)",
            "  );",
            "",
            "  integer current_case;",
            "",
            "  task clear_inputs;",
            "    begin",
            "      pred_valid = 1'b0; pred_class = 2'd0; snapshot_done = 1'b0; chunk_done = 1'b0;",
            "      class_mem_nsr = 64'sd0; class_mem_chf = 64'sd0; class_mem_arr = 64'sd0; class_mem_aff = 64'sd0;",
        ]
    )
    for field in FEATURE_FIELDS:
        lines.append(f"      {field} = 32'd0;")
    lines.extend(
        [
            "    end",
            "  endtask",
            "",
            "  task drive_snapshot;",
            "    input [1:0] pcls;",
            "    input is_last;",
        ]
    )
    for field in FEATURE_FIELDS:
        lines.append(f"    input [31:0] in_{field};")
    lines.extend(
        [
            "    begin",
            "      @(negedge clk);",
            "      pred_valid = 1'b1; pred_class = pcls; snapshot_done = 1'b1; chunk_done = is_last;",
        ]
    )
    for field in FEATURE_FIELDS:
        lines.append(f"      {field} = in_{field};")
    lines.extend(
        [
            "      @(negedge clk);",
            "      clear_inputs();",
            "      repeat (5) @(negedge clk);",
            "    end",
            "  endtask",
            "",
            "  always @(posedge clk) begin",
            "    if (final_valid) begin",
            '      $display("RESULT,%0d,%0d,%0d,%0d,%0d,%0d", current_case, final_pred_class, final_mem_nsr, final_mem_chf, final_mem_arr, final_mem_aff);',
            "    end",
            "  end",
            "",
            "  initial begin",
            '    $display("TB_START locked final membrane");',
            "    clear_inputs();",
            "    repeat (4) @(negedge clk);",
            "    rst = 1'b0;",
        ]
    )
    for index, selected_case in enumerate(selected):
        case_id = selected_case["case_id"]
        rows = selected_rows[case_id]
        lines.extend(
            [
                f"    // case_id {case_id}",
                f"    current_case = {index};",
                "    @(negedge clk); clear = 1'b1;",
                "    @(negedge clk); clear = 1'b0;",
            ]
        )
        for row_idx, row in enumerate(rows):
            is_last = "1'b1" if row_idx == len(rows) - 1 else "1'b0"
            pred_class = i(row, "snapshot_pred_class")
            values = ", ".join(verilog_value(i(row, field)) for field in FEATURE_FIELDS)
            lines.append(f"    drive_snapshot(2'd{pred_class}, {is_last}, {values});")
        lines.append("    repeat (10) @(negedge clk);")
    lines.extend(
        [
            '    $display("TB_DONE");',
            "    $finish;",
            "  end",
            "endmodule",
            "",
        ]
    )
    tb.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return tb


def parse_results(log_path: Path, selected: list[dict[str, Any]], expected: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pattern = re.compile(r"RESULT,(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+)")
    by_index: dict[int, tuple[int, int, int, int, int]] = {}
    for match in pattern.finditer(log_path.read_text(encoding="utf-8", errors="replace")):
        idx = int(match.group(1))
        by_index[idx] = tuple(int(match.group(i)) for i in range(2, 7))  # type: ignore[assignment]

    pred_rows: list[dict[str, Any]] = []
    mismatch_rows: list[dict[str, Any]] = []
    for idx, selected_case in enumerate(selected):
        case_id = selected_case["case_id"]
        exp = expected[case_id]
        got = by_index.get(idx)
        row = {
            **exp,
            "xsim_index": idx,
            "xsim_status": "ok" if got is not None else "missing",
        }
        if got is None:
            row.update(
                {
                    "xsim_pred_class": "",
                    "xsim_final_mem_NSR": "",
                    "xsim_final_mem_CHF": "",
                    "xsim_final_mem_ARR": "",
                    "xsim_final_mem_AFF": "",
                }
            )
            mismatch_rows.append({**row, "mismatch_reason": "missing_result"})
        else:
            pred, nsr, chf, arr, aff = got
            row.update(
                {
                    "xsim_pred_class": pred,
                    "xsim_final_mem_NSR": nsr,
                    "xsim_final_mem_CHF": chf,
                    "xsim_final_mem_ARR": arr,
                    "xsim_final_mem_AFF": aff,
                }
            )
            if (
                pred != exp["python_pred_class"]
                or nsr != exp["python_final_mem_NSR"]
                or chf != exp["python_final_mem_CHF"]
                or arr != exp["python_final_mem_ARR"]
                or aff != exp["python_final_mem_AFF"]
            ):
                mismatch_rows.append({**row, "mismatch_reason": "pred_or_mem"})
        pred_rows.append(row)
    return pred_rows, mismatch_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", choices=["train", "val", "test"], default="test")
    parser.add_argument("--max-cases", type=int, default=None)
    args = parser.parse_args()

    if not XVLOG.exists() or not XELAB.exists() or not XSIM.exists():
        reason = "Vivado/XSim 2020.2 executables were not found under C:/Xilinx/Vivado/2020.2/bin"
        write_not_run(reason)
        print(SUMMARY_MD)
        return 0

    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True, exist_ok=True)

    selected, expected, selected_rows = select_cases(args.split, args.max_cases)
    if not selected:
        raise SystemExit(f"no cases selected for split={args.split}")
    tb = write_tb(selected, selected_rows)
    tcl = WORK / "run.tcl"
    tcl.write_text("run all\nquit\n", encoding="utf-8")

    run(
        [
            str(XVLOG),
            "--nolog",
            "-i",
            slash(REPO / "rtl"),
            slash(REPO / "rtl" / "final_membrane_layer.v"),
            slash(tb),
        ],
        WORK,
        WORK / "xvlog.log",
    )
    run([str(XELAB), "--nolog", "-debug", "typical", "tb_locked_final_membrane", "-s", "tb_locked_final_membrane"], WORK, WORK / "xelab.log")
    run([str(XSIM), "tb_locked_final_membrane", "--nolog", "-tclbatch", "run.tcl"], WORK, WORK / "xsim.log")

    pred_rows, mismatch_rows = parse_results(WORK / "xsim.log", selected, expected)
    if not mismatch_rows:
        mismatch_rows = [{"status": "pass", "mismatch_count": 0, "cases": len(selected)}]
    write_csv(PRED_CSV, pred_rows)
    write_csv(MISMATCH_CSV, mismatch_rows)

    mismatch_count = 0 if mismatch_rows and mismatch_rows[0].get("status") == "pass" else len(mismatch_rows)
    pred_mismatches = sum(
        1
        for row in pred_rows
        if row.get("xsim_pred_class") != "" and int(row["xsim_pred_class"]) != int(row["python_pred_class"])
    )
    mem_mismatches = sum(
        1
        for row in pred_rows
        if row.get("xsim_pred_class") != ""
        and (
            int(row["xsim_final_mem_NSR"]) != int(row["python_final_mem_NSR"])
            or int(row["xsim_final_mem_CHF"]) != int(row["python_final_mem_CHF"])
            or int(row["xsim_final_mem_ARR"]) != int(row["python_final_mem_ARR"])
            or int(row["xsim_final_mem_AFF"]) != int(row["python_final_mem_AFF"])
        )
    )
    summary = {
        "status": "pass" if mismatch_count == 0 else "fail",
        "split": args.split,
        "case_count": len(selected),
        "max_cases": args.max_cases,
        "final_pred_mismatch": pred_mismatches,
        "final_mem_mismatch": mem_mismatches,
        "mismatch_rows": mismatch_count,
        "xvlog_log": str((WORK / "xvlog.log").relative_to(REPO)),
        "xelab_log": str((WORK / "xelab.log").relative_to(REPO)),
        "xsim_log": str((WORK / "xsim.log").relative_to(REPO)),
        "predictions": str(PRED_CSV.relative_to(REPO)),
        "mismatch": str(MISMATCH_CSV.relative_to(REPO)),
    }
    write_json(SUMMARY_JSON, summary)

    SUMMARY_MD.write_text(
        "\n".join(
            [
                "# XSim Locked Model Summary",
                "",
                "| 항목 | 결과 |",
                "|---|---|",
                f"| status | `{summary['status']}` |",
                f"| split | `{args.split}` |",
                f"| case_count | `{len(selected)}` |",
                f"| final_pred_mismatch | `{pred_mismatches}` |",
                f"| final_mem_mismatch | `{mem_mismatches}` |",
                f"| predictions | `{PRED_CSV.relative_to(REPO)}` |",
                f"| mismatch | `{MISMATCH_CSV.relative_to(REPO)}` |",
                f"| xsim_log | `{(WORK / 'xsim.log').relative_to(REPO)}` |",
                "",
                "## Interpretation",
                "",
                "이 결과는 locked Final Membrane RTL 단독 계층이 Python golden과 동일한 snapshot evidence stream을 받을 때 final prediction 및 final membrane vector가 일치하는지 확인한다.",
                "full top-level ECG stream XSim, Vivado implementation, Vitis board replay를 대체하지 않는다.",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )

    write_log("run_xsim_strict_recordwise", sys.argv, [SUMMARY_MD, MISMATCH_CSV, PRED_CSV, SUMMARY_JSON], summary)
    print(SUMMARY_MD)
    return 0 if mismatch_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
