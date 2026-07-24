#!/usr/bin/env python3
"""Run full-top XSim for the locked class-wise board replay cases.

This is intentionally separate from the standalone final_membrane_layer check:
it drives the same 30-minute .mem streams through snn_ecg_30min_final_top, so
the expected values match the RTL/Vitis board replay path rather than a compact
snapshot-evidence dump.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "reports" / "final_submission" / "fulltop_xsim_locked_class_cases"
DEFAULT_RESULTS = RESULTS
BOARD_COMPARISONS = REPO / "reports" / "board_replay" / "comparisons"
BOARD_36_COMPARISON = REPO / "reports" / "final" / "board_replay_36_expected_vs_board.csv"
EXPECTED_DIR = REPO / "reports" / "board_replay" / "locked_expected"

XVLOG = Path(r"C:\Xilinx\Vivado\2020.2\bin\xvlog.bat")
XELAB = Path(r"C:\Xilinx\Vivado\2020.2\bin\xelab.bat")
XSIM = Path(r"C:\Xilinx\Vivado\2020.2\bin\xsim.bat")

CORE_SOURCES = [
    "ecg_event_encoder.v",
    "ecg_event_encoder_adaptive.v",
    "snn_ecg_input_normalizer.v",
    "qrs_lif_detector.v",
    "pnn_rhythm_predictor.v",
    "dscr_spike_counter.v",
    "ram_peak_accumulator.v",
    "rdm_variability_neuron.v",
    "ectopic_pair_neuron.v",
    "qrs_maf_neuron.v",
    "rbbb_qrs_delay_bank.v",
    "abandoned_feature_stubs.v",
    "class_score_neurons.v",
    "snn_ecg_3feat_top.v",
]

CASES = [
    {
        "case_name": "locked_nsr_case117",
        "case_id": "117",
        "expected_class": 0,
        "mem": REPO / "fullrec_afe_30min_annotation_valid_balanced/test/NSR/16786/16786_30min_w035.mem",
    },
    {
        "case_name": "locked_chf_case91",
        "case_id": "91",
        "expected_class": 1,
        "mem": REPO / "fullrec_afe_30min_annotation_valid_balanced/test/CHF/chf09/chf09_30min_w029.mem",
    },
    {
        "case_name": "locked_arr_case45",
        "case_id": "45",
        "expected_class": 2,
        "mem": REPO / "fullrec_afe_30min_annotation_valid_balanced/test/ARR/118/118_30min_w000.mem",
    },
    {
        "case_name": "locked_aff_case16",
        "case_id": "16",
        "expected_class": 3,
        "mem": REPO / "fullrec_afe_30min_annotation_valid_balanced/test/AFF/06995/06995_30min_w016.mem",
    },
]


def slash(path: Path) -> str:
    return str(path).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_cases_from_csv(path: Path, case_ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows = read_csv(path)
    cases: list[dict[str, Any]] = []
    for row in rows:
        case_name = row["case_id"]
        if case_ids is not None and case_name not in case_ids:
            continue
        cases.append(
            {
                "case_name": case_name,
                "case_id": row.get("source_prediction_case_id") or case_name,
                "expected_class": int(row["class_id"]),
                "mem": REPO / row["mem_path"],
            }
        )
    if not cases:
        raise SystemExit(f"no cases selected from {path}")
    return cases


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(cmd: list[str], cwd: Path, log_path: Path) -> None:
    with log_path.open("w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}; see {log_path}")


def write_manifest(work: Path) -> Path:
    manifest = work / "locked_class_cases_manifest.txt"
    lines: list[str] = []
    for case in CASES:
        mem = Path(case["mem"])
        if not mem.exists():
            raise FileNotFoundError(mem)
        mem_ref = Path(os.path.relpath(mem, work))
        lines.append(f"{case['case_id']} {case['expected_class']} 1800000 {slash(mem_ref)}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return manifest


def write_wrapper(work: Path, manifest: Path, result_csv: Path, sample_gap_cycles: int) -> Path:
    wrapper = work / "tb_locked_fulltop_class_cases.v"
    manifest_ref = Path(os.path.relpath(manifest, work))
    result_ref = Path(os.path.relpath(result_csv, work))
    wrapper.write_text(
        f"""`timescale 1ns/1ps

module tb_locked_fulltop_class_cases;
    tb_snn_ecg_30min_chunk_dataset #(
        .MAX_SAMPLES(1800000),
        .MANIFEST_FILE("{slash(manifest_ref)}"),
        .RESULT_CSV("{slash(result_ref)}"),
        .DUT_SNAPSHOT_SAMPLES(60000),
        .DUT_SNAPSHOTS_PER_CHUNK(30),
        .DUT_POST_DONE_TICKS(37),
        .DUT_PROFILE_EN(1),
        .DUT_SAMPLE_GAP_CYCLES({sample_gap_cycles})
    ) tb();
endmodule
""",
        encoding="utf-8",
        newline="\n",
    )
    return wrapper


def write_project(work: Path, wrapper: Path) -> tuple[Path, Path]:
    prj = work / "sources_locked_fulltop_class_cases.prj"
    lines = [f'verilog work "{slash(REPO / "rtl" / "core" / src)}"' for src in CORE_SOURCES]
    lines.extend(
        [
            f'verilog work "{slash(REPO / "rtl" / "final_membrane_layer.v")}"',
            f'verilog work "{slash(REPO / "rtl" / "snn_ecg_30min_final_top.v")}"',
            f'verilog work "{slash(REPO / "sim" / "tb_snn_ecg_30min_chunk_dataset.v")}"',
            f'verilog work "{slash(wrapper)}"',
        ]
    )
    prj.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    tcl = work / "run.tcl"
    tcl.write_text("run all\nquit\n", encoding="utf-8", newline="\n")
    return prj, tcl


def load_board_case(case_name: str) -> dict[str, int] | None:
    path = BOARD_COMPARISONS / f"{case_name}_expected_vs_board.csv"
    if not path.exists():
        if not BOARD_36_COMPARISON.exists():
            return None
        for row in read_csv(BOARD_36_COMPARISON):
            if row.get("case_id") != case_name:
                continue
            samples_sent = int(row["samples_sent"])
            samples_accepted = int(row["samples_accepted"])
            return {
                "final_pred": int(row["board_final_pred"]),
                "final_mem_NSR": int(row["board_final_mem_NSR"]),
                "final_mem_CHF": int(row["board_final_mem_CHF"]),
                "final_mem_ARR": int(row["board_final_mem_ARR"]),
                "final_mem_AFF": int(row["board_final_mem_AFF"]),
                "samples_received": samples_sent,
                "samples_sent_to_ip": samples_sent,
                "samples_accepted": samples_accepted,
                "samples_consumed": samples_accepted,
                "snapshot_count": int(row["snapshot_count"]),
                "decision_count": 1,
            }
        return None
    out: dict[str, int] = {}
    for row in read_csv(path):
        board = row.get("board")
        if board not in ("", None):
            out[row["metric"]] = int(board)
    return out


def write_expected_jsons(xsim_rows: list[dict[str, str]]) -> None:
    by_case = {case["case_id"]: case for case in CASES}
    for row in xsim_rows:
        case = by_case.get(row["case_id"])
        if case is None:
            continue
        payload = {
            "case_name": case["case_name"],
            "case_id": row["case_id"],
            "expected_class": int(row["expected_class"]),
            "final_pred": int(row["final_pred_class"]),
            "final_mem": {
                "NSR": int(row["final_mem_NSR"]),
                "CHF": int(row["final_mem_CHF"]),
                "ARR": int(row["final_mem_ARR"]),
                "AFF": int(row["final_mem_AFF"]),
            },
            "samples": int(row["samples_driven"]),
            "snapshot_count": int(row["prof_windows"]),
            "decision_count": int(row["prof_decisions"]),
            "source": "full-top RTL XSim locked class-wise replay",
        }
        out = EXPECTED_DIR / f"{case['case_name']}_fulltop_xsim_expected_result.json"
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_summary(result_csv: Path, summary_json: Path, summary_md: Path) -> None:
    xsim_rows = read_csv(result_csv)
    board_rows: list[dict[str, Any]] = []
    all_pred_match = True
    all_mem_match = True
    all_transport_ok = True

    for row in xsim_rows:
        case = next(item for item in CASES if item["case_id"] == row["case_id"])
        board = load_board_case(str(case["case_name"]))
        if board is None:
            board_rows.append(
                {
                    "case_name": case["case_name"],
                    "case_id": row["case_id"],
                    "class_id": row["expected_class"],
                    "status": "board_missing",
                }
            )
            all_pred_match = False
            all_mem_match = False
            all_transport_ok = False
            continue

        x_mem = {
            "NSR": int(row["final_mem_NSR"]),
            "CHF": int(row["final_mem_CHF"]),
            "ARR": int(row["final_mem_ARR"]),
            "AFF": int(row["final_mem_AFF"]),
        }
        b_mem = {
            "NSR": board.get("final_mem_NSR"),
            "CHF": board.get("final_mem_CHF"),
            "ARR": board.get("final_mem_ARR"),
            "AFF": board.get("final_mem_AFF"),
        }
        pred_match = board.get("final_pred") == int(row["final_pred_class"])
        mem_match = all(b_mem[cls] == x_mem[cls] for cls in ("NSR", "CHF", "ARR", "AFF"))
        transport_ok = all(
            board.get(metric) == 1800000
            for metric in ("samples_received", "samples_sent_to_ip", "samples_accepted", "samples_consumed")
        ) and board.get("snapshot_count") == 30 and board.get("decision_count") == 1
        all_pred_match = all_pred_match and pred_match
        all_mem_match = all_mem_match and mem_match
        all_transport_ok = all_transport_ok and transport_ok
        board_rows.append(
            {
                "case_name": case["case_name"],
                "case_id": row["case_id"],
                "class_id": row["expected_class"],
                "xsim_final_pred": int(row["final_pred_class"]),
                "board_final_pred": board.get("final_pred"),
                "final_pred_match": int(pred_match),
                "xsim_final_mem_NSR": x_mem["NSR"],
                "xsim_final_mem_CHF": x_mem["CHF"],
                "xsim_final_mem_ARR": x_mem["ARR"],
                "xsim_final_mem_AFF": x_mem["AFF"],
                "board_final_mem_NSR": b_mem["NSR"],
                "board_final_mem_CHF": b_mem["CHF"],
                "board_final_mem_ARR": b_mem["ARR"],
                "board_final_mem_AFF": b_mem["AFF"],
                "final_mem_match": int(mem_match),
                "transport_ok": int(transport_ok),
            }
        )

    compare_csv = RESULTS / "locked_class_cases_xsim_vs_board.csv"
    write_csv(compare_csv, board_rows)
    summary = {
        "case_count": len(xsim_rows),
        "all_transport_ok": all_transport_ok,
        "all_final_pred_match": all_pred_match,
        "all_final_mem_match": all_mem_match,
        "xsim_predictions": str(result_csv.relative_to(REPO)).replace("\\", "/"),
        "xsim_vs_board": str(compare_csv.relative_to(REPO)).replace("\\", "/"),
    }
    summary_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Locked Full-Top XSim vs Board Replay Summary",
        "",
        "| case | class | transport | final_pred | final_mem | XSim final_mem | Board final_mem |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for row in board_rows:
        lines.append(
            f"| {row['case_name']} | {row['class_id']} | {row.get('transport_ok', 0)} | "
            f"{row.get('final_pred_match', 0)} | {row.get('final_mem_match', 0)} | "
            f"{row.get('xsim_final_mem_NSR')}/{row.get('xsim_final_mem_CHF')}/{row.get('xsim_final_mem_ARR')}/{row.get('xsim_final_mem_AFF')} | "
            f"{row.get('board_final_mem_NSR')}/{row.get('board_final_mem_CHF')}/{row.get('board_final_mem_ARR')}/{row.get('board_final_mem_AFF')} |"
        )
    lines.extend(
        [
            "",
            f"- XSim predictions: `{result_csv.relative_to(REPO)}`",
            f"- XSim vs board CSV: `{compare_csv.relative_to(REPO)}`",
            f"- all_transport_ok: `{all_transport_ok}`",
            f"- all_final_pred_match: `{all_pred_match}`",
            f"- all_final_mem_match: `{all_mem_match}`",
            "",
        ]
    )
    summary_md.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    global CASES, RESULTS

    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-run", action="store_true", help="reuse existing XSim result CSV")
    parser.add_argument("--sample-gap-cycles", type=int, default=0, help="idle cycles inserted between accepted samples in direct full-top XSim")
    parser.add_argument("--results-dir", type=Path, default=RESULTS, help="directory for XSim outputs")
    parser.add_argument("--cases-csv", type=Path, default=None, help="optional board_replay_36_cases.csv manifest")
    parser.add_argument("--case-id", action="append", default=[], help="case_id from --cases-csv to include")
    args = parser.parse_args()
    RESULTS = args.results_dir.resolve()
    if args.cases_csv is not None:
        selected = set(args.case_id) if args.case_id else None
        CASES = load_cases_from_csv(args.cases_csv.resolve(), selected)

    work = RESULTS / "work"
    result_csv = RESULTS / "locked_class_cases_fulltop_xsim_predictions.csv"
    summary_json = RESULTS / "locked_class_cases_xsim_vs_board_summary.json"
    summary_md = RESULTS / "locked_class_cases_xsim_vs_board_summary.md"
    metadata_json = RESULTS / "locked_class_cases_fulltop_xsim_metadata.json"

    RESULTS.mkdir(parents=True, exist_ok=True)
    if not args.skip_run:
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True, exist_ok=True)
        manifest = write_manifest(work)
        wrapper = write_wrapper(work, manifest, result_csv, args.sample_gap_cycles)
        prj, tcl = write_project(work, wrapper)
        run([str(XVLOG), "--nolog", "-i", slash(REPO / "rtl"), "-prj", slash(prj)], work, RESULTS / "xvlog.log")
        run([str(XELAB), "--nolog", "-debug", "typical", "tb_locked_fulltop_class_cases", "-s", "tb_locked_fulltop_class_cases"], work, RESULTS / "xelab.log")
        run([str(XSIM), "tb_locked_fulltop_class_cases", "--nolog", "-tclbatch", "{" + slash(tcl) + "}"], work, RESULTS / "xsim.log")

    if not result_csv.exists():
        raise FileNotFoundError(result_csv)
    xsim_rows = read_csv(result_csv)
    metadata = {
        "source": "snn_ecg_30min_final_top full-top XSim",
        "sample_gap_cycles": args.sample_gap_cycles,
        "case_count": len(xsim_rows),
        "cases_csv": None if args.cases_csv is None else str(args.cases_csv.resolve().relative_to(REPO)).replace("\\", "/"),
        "result_csv": str(result_csv.relative_to(REPO)).replace("\\", "/"),
    }
    metadata_json.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if args.sample_gap_cycles == 0 and RESULTS == DEFAULT_RESULTS.resolve():
        write_expected_jsons(xsim_rows)
    write_summary(result_csv, summary_json, summary_md)
    print(summary_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
