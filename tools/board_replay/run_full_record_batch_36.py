#!/usr/bin/env python3
"""Run or prepare the 36-case strict final_test board replay batch.

The script intentionally treats a generated manifest as preparation only.
Board completion is counted only from raw UART transcripts parsed and compared
against the locked Python/XSim expected final outputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]
DEFAULT_CASES = REPO / "reports" / "final" / "board_replay_36_cases.csv"
DEFAULT_OUTPUT_DIR = REPO / "reports" / "final" / "board_replay_36"
DEFAULT_COMPARISON = REPO / "reports" / "final" / "board_replay_36_expected_vs_board.csv"
DEFAULT_SUMMARY_MD = REPO / "reports" / "final" / "board_replay_36_batch_summary.md"
DEFAULT_SUMMARY_JSON = REPO / "reports" / "final" / "board_replay_36_batch_summary.json"
EXPECTED_SAMPLES = 1_800_000
EXPECTED_SNAPSHOTS = 30
EXPECTED_DECISIONS = 1
CLASS_LABELS = ["NSR", "CHF", "ARR", "AFF"]


def load_single_sender_module() -> Any:
    path = REPO / "tools" / "board_replay" / "send_full_record_uart.py"
    spec = importlib.util.spec_from_file_location("send_full_record_uart", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SINGLE = load_single_sender_module()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO)).replace("\\", "/")


def parse_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def expected_from_case(case: dict[str, str]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "class_label": case["class_label"],
        "class_id": int(case["class_id"]),
        "ground_truth_label": case["ground_truth_label"],
        "expected_final_pred": int(case["expected_final_pred"]),
        "expected_final_pred_name": case["expected_final_pred_name"],
        "final_mem": {
            "NSR": int(case["expected_final_mem_NSR"]),
            "CHF": int(case["expected_final_mem_CHF"]),
            "ARR": int(case["expected_final_mem_ARR"]),
            "AFF": int(case["expected_final_mem_AFF"]),
        },
        "samples": int(case["sample_count_expected"]),
        "snapshot_count": int(case["snapshot_count_expected"]),
        "decision_count": EXPECTED_DECISIONS,
    }


def validate_cases(cases: list[dict[str, str]]) -> None:
    if len(cases) != 36:
        raise SystemExit(f"expected 36 cases, got {len(cases)}")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    class_counts = {label: 0 for label in CLASS_LABELS}
    required = [
        "case_id",
        "class_label",
        "class_id",
        "source_record_id",
        "chunk_id",
        "mem_path",
        "expected_final_pred",
        "expected_final_mem_NSR",
        "expected_final_mem_CHF",
        "expected_final_mem_ARR",
        "expected_final_mem_AFF",
        "ground_truth_label",
        "sample_count_expected",
        "snapshot_count_expected",
    ]
    for case in cases:
        missing = [key for key in required if case.get(key) in (None, "")]
        if missing:
            raise SystemExit(f"{case.get('case_id', '<unknown>')} missing fields: {missing}")
        case_id = case["case_id"]
        mem_path = case["mem_path"]
        if case_id in seen_ids:
            raise SystemExit(f"duplicate case_id: {case_id}")
        if mem_path in seen_paths:
            raise SystemExit(f"duplicate mem_path: {mem_path}")
        seen_ids.add(case_id)
        seen_paths.add(mem_path)
        label = case["class_label"]
        if label not in class_counts:
            raise SystemExit(f"{case_id} invalid class_label: {label}")
        class_counts[label] += 1
        path = REPO / mem_path
        if not path.exists():
            raise SystemExit(f"{case_id} missing mem file: {path}")
        if int(case["sample_count_expected"]) != EXPECTED_SAMPLES:
            raise SystemExit(f"{case_id} sample_count_expected must be {EXPECTED_SAMPLES}")
        if int(case["snapshot_count_expected"]) != EXPECTED_SNAPSHOTS:
            raise SystemExit(f"{case_id} snapshot_count_expected must be {EXPECTED_SNAPSHOTS}")
    if class_counts != {label: 9 for label in CLASS_LABELS}:
        raise SystemExit(f"class balance must be 9 each, got {class_counts}")


def count_samples_and_hash(path: Path) -> tuple[int, str]:
    count = 0
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for raw in f:
            sha.update(raw)
            stripped = raw.split(b"#", 1)[0].split(b"//", 1)[0].strip()
            if stripped:
                count += 1
    return count, sha.hexdigest()


def board_value(board: dict[str, int], key: str) -> int | None:
    return board.get(key)


def compare_case(
    case: dict[str, str],
    board: dict[str, int] | None,
    internal_pass: bool,
    status: str,
    notes: str,
    transcript_path: Path | None,
    parsed_path: Path | None,
) -> dict[str, Any]:
    expected = expected_from_case(case)
    board = board or {}
    b_mem = {
        "NSR": board_value(board, "final_mem_nsr"),
        "CHF": board_value(board, "final_mem_chf"),
        "ARR": board_value(board, "final_mem_arr"),
        "AFF": board_value(board, "final_mem_aff"),
    }
    pred_match = board.get("final_pred") == expected["expected_final_pred"]
    mem_matches = {
        cls: (b_mem[cls] == expected["final_mem"][cls]) if b_mem[cls] is not None else False
        for cls in CLASS_LABELS
    }
    final_mem_exact_match = all(mem_matches.values())
    counters_ok = (
        board.get("samples_received") == expected["samples"]
        and board.get("samples_sent_to_ip") == expected["samples"]
        and board.get("samples_accepted") == expected["samples"]
        and board.get("samples_consumed") == expected["samples"]
        and board.get("snapshot_count") == expected["snapshot_count"]
        and board.get("decision_count") == expected["decision_count"]
        and board.get("final_valid") == 1
        and board.get("done") == 1
    )
    board_vs_expected_pass = (
        status == "completed"
        and internal_pass
        and counters_ok
        and pred_match
        and final_mem_exact_match
    )
    board_correct_vs_label = (
        board.get("final_pred") == int(case["class_id"])
        if board.get("final_pred") is not None
        else False
    )
    host_status = "PASS" if board_vs_expected_pass else status.upper()
    if status == "completed" and not board_vs_expected_pass:
        if not internal_pass:
            host_status = "BOARD_FAIL"
        elif not counters_ok:
            host_status = "INVALID_COUNTERS"
        elif not pred_match:
            host_status = "PRED_MISMATCH"
        elif not final_mem_exact_match:
            host_status = "FINAL_MEM_MISMATCH"
    return {
        "case_id": case["case_id"],
        "class_label": case["class_label"],
        "source_record_id": case["source_record_id"],
        "mem_path": case["mem_path"],
        "expected_final_pred": expected["expected_final_pred"],
        "board_final_pred": "" if board.get("final_pred") is None else board["final_pred"],
        "pred_match": int(pred_match) if status == "completed" else "",
        "expected_final_mem_NSR": expected["final_mem"]["NSR"],
        "board_final_mem_NSR": "" if b_mem["NSR"] is None else b_mem["NSR"],
        "mem_NSR_match": int(mem_matches["NSR"]) if status == "completed" else "",
        "expected_final_mem_CHF": expected["final_mem"]["CHF"],
        "board_final_mem_CHF": "" if b_mem["CHF"] is None else b_mem["CHF"],
        "mem_CHF_match": int(mem_matches["CHF"]) if status == "completed" else "",
        "expected_final_mem_ARR": expected["final_mem"]["ARR"],
        "board_final_mem_ARR": "" if b_mem["ARR"] is None else b_mem["ARR"],
        "mem_ARR_match": int(mem_matches["ARR"]) if status == "completed" else "",
        "expected_final_mem_AFF": expected["final_mem"]["AFF"],
        "board_final_mem_AFF": "" if b_mem["AFF"] is None else b_mem["AFF"],
        "mem_AFF_match": int(mem_matches["AFF"]) if status == "completed" else "",
        "final_mem_exact_match": int(final_mem_exact_match) if status == "completed" else "",
        "samples_expected": expected["samples"],
        "samples_sent": "" if board.get("samples_received") is None else board["samples_received"],
        "samples_accepted": "" if board.get("samples_accepted") is None else board["samples_accepted"],
        "snapshot_expected": expected["snapshot_count"],
        "snapshot_count": "" if board.get("snapshot_count") is None else board["snapshot_count"],
        "done": "" if board.get("done") is None else board["done"],
        "board_vs_expected_pass": int(board_vs_expected_pass) if status == "completed" else 0,
        "ground_truth_label": case["ground_truth_label"],
        "board_correct_vs_label": int(board_correct_vs_label) if status == "completed" else "",
        "transcript_path": "" if transcript_path is None else rel(transcript_path),
        "parsed_json_path": "" if parsed_path is None else rel(parsed_path),
        "status": host_status,
        "notes": notes,
    }


def write_case_parsed(
    path: Path,
    case: dict[str, str],
    board: dict[str, int] | None,
    internal_pass: bool,
    status: str,
    notes: str,
    transcript_path: Path | None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "case_id": case["case_id"],
        "status": status,
        "notes": notes,
        "board_internal_pass": internal_pass,
        "transcript_path": None if transcript_path is None else rel(transcript_path),
        "expected": expected_from_case(case),
        "board": board or {},
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_case(case: dict[str, str], args: argparse.Namespace, output_dir: Path) -> tuple[dict[str, int] | None, bool, str, str, Path | None, Path]:
    mem_path = REPO / case["mem_path"]
    transcript_path = output_dir / "transcripts" / f"{case['case_id']}.txt"
    parsed_path = output_dir / "parsed" / f"{case['case_id']}.json"
    if args.dry_run:
        sample_count, sha = count_samples_and_hash(mem_path)
        notes = "dry-run only; no board transcript captured"
        if sample_count != EXPECTED_SAMPLES:
            notes = f"dry-run sample count mismatch: {sample_count}"
            return None, False, "invalid_manifest", notes, None, parsed_path
        if case.get("mem_sha256") and case["mem_sha256"] != sha:
            notes = "dry-run SHA-256 mismatch against manifest"
            return None, False, "invalid_manifest", notes, None, parsed_path
        return None, False, "not_run", notes, None, parsed_path

    payload, sample_count = SINGLE.load_mem_payload(mem_path, args.max_samples)
    if sample_count != EXPECTED_SAMPLES:
        notes = f"sample count mismatch before UART send: {sample_count}"
        return None, False, "invalid_manifest", notes, None, parsed_path

    serial = SINGLE.import_serial()
    ser = serial.Serial(args.port, args.baud, timeout=0.1, write_timeout=args.write_timeout_sec)
    monitor = SINGLE.SerialMonitor(ser)
    monitor.start()
    board: dict[str, int] | None = None
    internal_pass = False
    status = "completed"
    notes = ""
    try:
        try:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        except Exception:
            pass
        if args.program_each_case:
            rc = SINGLE.program_board(args.bit.resolve(), args.elf.resolve())
            if rc != 0:
                raise RuntimeError(f"XSDB program/download failed with exit code {rc}")
        ready_deadline = time.monotonic() + args.ready_timeout
        total_match = None
        while time.monotonic() < ready_deadline:
            total_match = SINGLE.re.search(r"SNN_ECG_FULL_REPLAY_READY total_samples=(\d+)\r?\n", monitor.text())
            if total_match is not None:
                break
            time.sleep(0.05)
        if total_match is None:
            raise TimeoutError(f"READY marker with total_samples not seen within {args.ready_timeout}s")
        board_total = int(total_match.group(1)) if total_match else None
        if board_total != EXPECTED_SAMPLES:
            raise RuntimeError(f"board total_samples={board_total}, expected {EXPECTED_SAMPLES}")
        SINGLE.send_payload(
            ser,
            monitor,
            payload,
            args.flow_chunk_samples,
            args.progress_samples,
            args.ack_timeout,
        )
        terminal = monitor.wait_for_any(
            ["SNN_ECG_FULL_REPLAY_BOARD_PASS", "SNN_ECG_FULL_REPLAY_BOARD_FAIL"],
            args.timeout_sec,
        )
        if terminal is None:
            raise TimeoutError(f"PASS/FAIL marker not seen within {args.timeout_sec}s")
    except Exception as exc:
        status = "error"
        notes = str(exc)
    finally:
        time.sleep(0.5)
        monitor.stop()
        ser.close()

    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript = (
        f"HOST_CASE case_id={case['case_id']} class_label={case['class_label']} "
        f"mem_path={case['mem_path']}\n"
        + monitor.text()
    )
    transcript_path.write_text(transcript, encoding="utf-8", newline="\n")
    board = SINGLE.parse_board_values(transcript)
    internal_pass = "SNN_ECG_FULL_REPLAY_BOARD_PASS" in transcript
    if status == "error" and board:
        notes = f"{notes}; partial transcript parsed"
    return board, internal_pass, status, notes, transcript_path, parsed_path


def summarize(results: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    completed = [row for row in results if row["status"] in {"PASS", "BOARD_FAIL", "INVALID_COUNTERS", "PRED_MISMATCH", "FINAL_MEM_MISMATCH"}]
    pass_rows = [row for row in results if row["board_vs_expected_pass"] == 1]
    pred_matches = [row for row in completed if row["pred_match"] == 1]
    mem_matches = [row for row in completed if row["final_mem_exact_match"] == 1]
    label_correct = [row for row in completed if row["board_correct_vs_label"] == 1]
    failed = [row for row in results if row["status"] not in {"PASS", "NOT_RUN"}]
    pending = [row for row in results if row["status"] == "NOT_RUN"]
    final_mem_mismatch = [row for row in results if row["status"] == "FINAL_MEM_MISMATCH"]
    status = "completed" if len(completed) == 36 else ("partial" if completed else "pending")
    validation_result = "not_run"
    if status == "completed":
        validation_result = "pass" if len(pass_rows) == 36 else "fail"
    elif completed or failed:
        validation_result = "invalid" if failed else "partial"
    return {
        "status": status,
        "validation_result": validation_result,
        "cases_requested": 36,
        "cases_completed": len(completed),
        "cases_passed": len(pass_rows),
        "cases_failed_or_invalid": len(failed),
        "cases_final_mem_mismatch": len(final_mem_mismatch),
        "cases_pending": len(pending),
        "samples_per_case": EXPECTED_SAMPLES,
        "snapshots_per_case": EXPECTED_SNAPSHOTS,
        "pred_match_correct": len(pred_matches),
        "pred_match_total": len(completed),
        "final_mem_match_correct": len(mem_matches),
        "final_mem_match_total": len(completed),
        "classification_correct": len(label_correct),
        "classification_total": len(completed),
        "classification_accuracy_percent": round(100.0 * len(label_correct) / len(completed), 2) if completed else None,
        "manifest_csv": rel(args.cases.resolve()),
        "output_dir": rel(args.output_dir.resolve()),
        "transcript_dir": rel((args.output_dir / "transcripts").resolve()),
        "parsed_dir": rel((args.output_dir / "parsed").resolve()),
        "csv_path": rel(args.comparison.resolve()),
        "summary_path": rel(args.summary_md.resolve()),
        "summary_json_path": rel(args.summary_json.resolve()),
        "uart_port": args.port,
        "baud": args.baud,
        "program_each_case": bool(args.program_each_case),
        "dry_run": bool(args.dry_run),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_summary_md(path: Path, summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    pred = f"{summary['pred_match_correct']}/{summary['pred_match_total']}" if summary["pred_match_total"] else "0/0"
    mem = (
        f"{summary['final_mem_match_correct']}/{summary['final_mem_match_total']}"
        if summary["final_mem_match_total"]
        else "0/0"
    )
    cls = (
        f"{summary['classification_correct']}/{summary['classification_total']}"
        if summary["classification_total"]
        else "0/0"
    )
    lines = [
        "# 36-case Strict Final Test Full-record Board Replay",
        "",
        "이 문서는 strict record-wise final_test 36개 30분 chunk에 대한 Vitis/MicroBlaze board replay batch 상태를 정리한다.",
        "실제 board transcript가 없는 case는 완료로 세지 않는다.",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Cases requested | {summary['cases_requested']} |",
        f"| Cases completed | {summary['cases_completed']} |",
        f"| Samples per case | {summary['samples_per_case']:,} |",
        f"| Snapshots per case | {summary['snapshots_per_case']} |",
        f"| Board-vs-expected final_pred PASS | {pred} |",
        f"| Board-vs-expected final_mem exact PASS | {mem} |",
        f"| Board classification accuracy vs label | {cls} |",
        f"| Pending cases | {summary['cases_pending']} |",
        f"| Final_mem exact mismatch cases | {summary['cases_final_mem_mismatch']} |",
        f"| Other failed/invalid cases | {summary['cases_failed_or_invalid'] - summary['cases_final_mem_mismatch']} |",
        "",
        "| case_id | label | expected_pred | board_pred | pred_match | mem_match | samples | snapshots | status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in results:
        lines.append(
            f"| `{row['case_id']}` | {row['class_label']} | {row['expected_final_pred']} | "
            f"{row['board_final_pred']} | {row['pred_match']} | {row['final_mem_exact_match']} | "
            f"{row['samples_sent']} | {row['snapshot_count']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "이 결과는 physical AFE/ADC 검증이 아니라, locked RTL/IP bitstream이 Vitis/MicroBlaze board path에서 full-record input stream을 끝까지 처리하는지 확인하는 board-level integration evidence이다.",
            "",
            "## Artifacts",
            "",
            f"- Case manifest: `{summary['manifest_csv']}`",
            f"- Expected-vs-board CSV: `{summary['csv_path']}`",
            f"- Batch summary JSON: `{summary['summary_json_path']}`",
            f"- Transcripts: `{summary['transcript_dir']}`",
            f"- Parsed JSON: `{summary['parsed_dir']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def update_final_metrics(summary: dict[str, Any]) -> None:
    path = REPO / "reports" / "final" / "final_metrics.json"
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    data["board_replay_36"] = {
        "status": summary["status"],
        "validation_result": summary["validation_result"],
        "cases_requested": summary["cases_requested"],
        "cases_completed": summary["cases_completed"],
        "cases_passed": summary["cases_passed"],
        "cases_failed_or_invalid": summary["cases_failed_or_invalid"],
        "cases_final_mem_mismatch": summary["cases_final_mem_mismatch"],
        "cases_pending": summary["cases_pending"],
        "samples_per_case": summary["samples_per_case"],
        "snapshots_per_case": summary["snapshots_per_case"],
        "pred_match_correct": summary["pred_match_correct"],
        "pred_match_total": summary["pred_match_total"],
        "final_mem_match_correct": summary["final_mem_match_correct"],
        "final_mem_match_total": summary["final_mem_match_total"],
        "classification_correct": summary["classification_correct"],
        "classification_total": summary["classification_total"],
        "classification_accuracy_percent": summary["classification_accuracy_percent"],
        "summary_path": summary["summary_path"],
        "csv_path": summary["csv_path"],
        "manifest_csv": summary["manifest_csv"],
        "manifest_json": "reports/final/board_replay_36_cases.json",
        "transcript_dir": summary["transcript_dir"],
        "parsed_dir": summary["parsed_dir"],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser(description="Run the strict final_test 36-case full-record board replay batch.")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--port", "--uart", dest="port", default=None)
    parser.add_argument("--baud", type=int, default=SINGLE.DEFAULT_BAUD)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--comparison", type=Path, default=None)
    parser.add_argument("--summary-md", type=Path, default=None)
    parser.add_argument("--summary-json", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--timeout-sec", type=float, default=900.0)
    parser.add_argument("--ready-timeout", type=float, default=60.0)
    parser.add_argument("--write-timeout-sec", type=float, default=10.0)
    parser.add_argument("--ack-timeout", type=float, default=30.0)
    parser.add_argument("--retry", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-program-each-case", dest="program_each_case", action="store_false")
    parser.set_defaults(program_each_case=True)
    parser.add_argument("--bit", type=Path, default=SINGLE.DEFAULT_BIT)
    parser.add_argument("--elf", type=Path, default=SINGLE.DEFAULT_ELF)
    parser.add_argument("--flow-chunk-samples", type=int, default=SINGLE.DEFAULT_FLOW_CHUNK_SAMPLES)
    parser.add_argument("--progress-samples", type=int, default=100000)
    parser.add_argument("--max-samples", type=int, default=None, help="debug only; must not be used for final evidence")
    parser.add_argument("--update-final-metrics", action="store_true")
    args = parser.parse_args()

    args.cases = args.cases.resolve()
    args.output_dir = args.output_dir.resolve()
    using_default_output = args.output_dir == DEFAULT_OUTPUT_DIR.resolve()
    if args.comparison is None:
        args.comparison = DEFAULT_COMPARISON if using_default_output else args.output_dir / "expected_vs_board.csv"
    if args.summary_md is None:
        args.summary_md = DEFAULT_SUMMARY_MD if using_default_output else args.output_dir / "batch_summary.md"
    if args.summary_json is None:
        args.summary_json = DEFAULT_SUMMARY_JSON if using_default_output else args.output_dir / "batch_summary.json"
    args.comparison = args.comparison.resolve()
    args.summary_md = args.summary_md.resolve()
    args.summary_json = args.summary_json.resolve()
    if not args.dry_run and not args.port:
        raise SystemExit("--port/--uart is required unless --dry-run is used")
    cases = read_csv(args.cases)
    validate_cases(cases)
    if args.case_id:
        wanted = set(args.case_id)
        cases = [case for case in cases if case["case_id"] in wanted]
        missing = wanted - {case["case_id"] for case in cases}
        if missing:
            raise SystemExit(f"case_id not found: {sorted(missing)}")
    if args.max_cases is not None:
        cases = cases[: args.max_cases]

    results: list[dict[str, Any]] = []
    for case in cases:
        parsed_path = args.output_dir / "parsed" / f"{case['case_id']}.json"
        if args.resume and parsed_path.exists():
            parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
            status = parsed.get("status", "not_run")
            transcript_path = parsed.get("transcript_path")
            transcript = REPO / transcript_path if transcript_path else None
            if status == "completed" and transcript is not None and transcript.exists():
                board = parsed.get("board") or {}
                internal_pass = bool(parsed.get("board_internal_pass", False))
                row = compare_case(case, board, internal_pass, status, "resume", transcript, parsed_path)
                results.append(row)
                continue
        attempts = args.retry + 1
        last: tuple[dict[str, int] | None, bool, str, str, Path | None, Path] | None = None
        for attempt in range(1, attempts + 1):
            last = run_case(case, args, args.output_dir)
            if last[2] in ("completed", "not_run", "invalid_manifest") or attempt == attempts:
                break
            time.sleep(2.0)
        assert last is not None
        board, internal_pass, status, notes, transcript_path, parsed_path = last
        write_case_parsed(parsed_path, case, board, internal_pass, status, notes, transcript_path)
        row = compare_case(case, board, internal_pass, status, notes, transcript_path, parsed_path)
        results.append(row)

    # Include not-run rows for unselected cases so the aggregate CSV always has 36 rows.
    selected_ids = {row["case_id"] for row in results}
    if len(results) != 36:
        for case in read_csv(args.cases):
            if case["case_id"] in selected_ids:
                continue
            parsed_path = args.output_dir / "parsed" / f"{case['case_id']}.json"
            row = compare_case(case, None, False, "not_run", "not selected in this invocation", None, parsed_path)
            results.append(row)

    order = {case["case_id"]: idx for idx, case in enumerate(read_csv(args.cases))}
    results.sort(key=lambda row: order.get(row["case_id"], 999))

    fields = [
        "case_id",
        "class_label",
        "source_record_id",
        "mem_path",
        "expected_final_pred",
        "board_final_pred",
        "pred_match",
        "expected_final_mem_NSR",
        "board_final_mem_NSR",
        "mem_NSR_match",
        "expected_final_mem_CHF",
        "board_final_mem_CHF",
        "mem_CHF_match",
        "expected_final_mem_ARR",
        "board_final_mem_ARR",
        "mem_ARR_match",
        "expected_final_mem_AFF",
        "board_final_mem_AFF",
        "mem_AFF_match",
        "final_mem_exact_match",
        "samples_expected",
        "samples_sent",
        "samples_accepted",
        "snapshot_expected",
        "snapshot_count",
        "done",
        "board_vs_expected_pass",
        "ground_truth_label",
        "board_correct_vs_label",
        "transcript_path",
        "parsed_json_path",
        "status",
        "notes",
    ]
    write_csv(args.comparison, results, fields)
    summary = summarize(results, args)
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_summary_md(args.summary_md, summary, results)
    if args.update_final_metrics:
        update_final_metrics(summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["validation_result"] in {"pass", "not_run", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
