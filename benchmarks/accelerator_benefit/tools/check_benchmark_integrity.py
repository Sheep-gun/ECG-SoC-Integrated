#!/usr/bin/env python3
"""Fail closed on benchmark scope, equivalence, and evidence violations."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "benchmarks" / "accelerator_benefit"
RESULTS = BENCH / "results"
REPORTS = BENCH / "reports"
CLASSES = ("NSR", "CHF", "ARR", "AFF")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_repetitions(rows: list[dict[str, str]], scope: str, failures: list[str]) -> None:
    by_case: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_case.setdefault(row.get("case_id", ""), []).append(row)
        if row.get("sample_count") != "1800000":
            failures.append(f"{scope} {row.get('case_id')}: sample_count != 1800000")
    if len(by_case) != 36:
        failures.append(f"{scope} case count {len(by_case)} != 36")
    expected_repeats = {str(i) for i in range(10)}
    for case_id, case_rows in by_case.items():
        if len(case_rows) != 10 or {row.get("repeat_id") for row in case_rows} != expected_repeats:
            failures.append(f"{scope} {case_id}: repetitions are not exactly 0..9")


def main() -> int:
    failures: list[str] = []
    hashes = {row["artifact"]: row["sha256"] for row in read_csv(RESULTS / "immutable_artifact_hashes.csv")}
    protected_prefixes = (
        "configs/", "rtl/", "reports/final/", "results/board_replay/",
    )
    for rel, expected in hashes.items():
        if not rel.startswith(protected_prefixes):
            continue
        path = REPO / rel
        if not path.exists() or digest(path) != expected:
            failures.append(f"locked artifact changed: {rel}")

    metrics = json.loads((REPO / "reports/final/final_metrics.json").read_text(encoding="utf-8-sig"))
    checks = {
        "final model": metrics.get("final_model_id") == "structural_guarded_silent_aff_1008710",
        "chunk metric": metrics.get("final_test_chunk", {}).get("correct") == 29 and metrics.get("final_test_chunk", {}).get("total") == 36,
        "record metric": metrics.get("final_test_record_majority", {}).get("correct") == 16 and metrics.get("final_test_record_majority", {}).get("total") == 19,
        "test count": metrics.get("test_evaluation_count") == 1,
        "test selection": metrics.get("test_used_for_selection") is False,
    }
    failures.extend(name for name, ok in checks.items() if not ok)

    rtl = read_csv(RESULTS / "rtl_cycle_benchmark.csv")
    if len(rtl) != 36:
        failures.append(f"RTL row count {len(rtl)} != 36")
    for row in rtl:
        case = row.get("case_id", "<unknown>")
        if row.get("sample_gap_cycles") != "2":
            failures.append(f"{case}: sample_gap_cycles != 2")
        if row.get("accepted_samples") != "1800000":
            failures.append(f"{case}: accepted_samples != 1800000")
        if row.get("windows") != "30":
            failures.append(f"{case}: windows != 30")
        if row.get("decisions") != "1":
            failures.append(f"{case}: decisions != 1")
        if row.get("final_pred_match") != "true" or row.get("final_mem_match") != "true":
            failures.append(f"{case}: RTL output mismatch")
        if not row.get("clock_frequency_hz"):
            failures.append(f"{case}: missing clock")

    board = read_csv(RESULTS / "existing_board_functional_audit.csv")
    if len(board) != 36:
        failures.append(f"board audit row count {len(board)} != 36")
    for row in board:
        if row.get("transcript_exists") != "true" or row.get("final_pred_match") != "1" or row.get("final_mem_match") != "1":
            failures.append(f"{row.get('case_id')}: board evidence misreported")
        if row.get("timing_measurement_present") != "false":
            failures.append(f"{row.get('case_id')}: old transcript incorrectly used as timing")

    summary = read_csv(RESULTS / "accelerator_benefit_summary.csv")
    if len(summary) != 8:
        failures.append(f"comparison row count {len(summary)} != 8")
    for row in summary:
        if not row.get("evidence_path"):
            failures.append(f"{row.get('implementation')}: missing evidence path")
        pending = row.get("status") == "PENDING_BOARD"
        if pending:
            for key in ("latency_ms_median", "throughput_samples_per_s", "power_w", "energy_per_decision_j"):
                if row.get(key) in ("0", "0.0", "0.000000"):
                    failures.append(f"{row.get('implementation')}: pending {key} represented as zero")
            if row.get("output_equivalence") != "PENDING_BOARD":
                failures.append(f"{row.get('implementation')}: pending equivalence misreported")
        speedup = row.get("speedup_vs_python_kernel")
        compatible_speedup = row.get("implementation") in {
            "Python integer kernel", "C/C++ exact RTL translation", "Pure RTL canonical cycle-derived",
        }
        if speedup not in ("", "N/A") and not compatible_speedup:
            failures.append(f"{row.get('implementation')}: incompatible-scope speedup present")
        if row.get("implementation") == "Existing FPGA functional replay" and row.get("latency_ms_median") != "N/A":
            failures.append("existing UART evidence incorrectly reports latency")

    power = read_csv(RESULTS / "power_energy_summary.csv")
    for row in power:
        if row["implementation"] == "Pure RTL" and "ESTIMATED" not in row["status"]:
            failures.append("estimated RTL power mislabeled")
        if row["implementation"] == "Physical FPGA board":
            if row["status"] != "PENDING_BOARD" or row["power_w"] == "0":
                failures.append("board power fabricated or zero-filled")
        if row["implementation"] == "CPU" and not row["status"].startswith("N/A"):
            failures.append("CPU energy reported without counter")

    board_build_status = json.loads((BENCH / "board/build/build_status.json").read_text(encoding="utf-8"))
    if board_build_status.get("status") == "built":
        built_elf = BENCH / "board/build/snn_ecg_mb_full_replay_benchmark.elf"
        if not built_elf.exists() or digest(built_elf) != board_build_status.get("elf_sha256"):
            failures.append("instrumented board ELF missing or hash mismatch")

    cpu_env = json.loads((RESULTS / "cpu_environment.json").read_text(encoding="utf-8"))
    cpu_rows = read_csv(RESULTS / "cpu_python_kernel_runs.csv")
    e2e_rows = read_csv(RESULTS / "cpu_python_end_to_end_runs.csv")
    if cpu_env["status"] != "COMPLETED":
        failures.append(f"Python benchmark status is {cpu_env['status']}, not COMPLETED")
    if cpu_env["status"].startswith("NOT_COMPLETED") and cpu_rows:
        failures.append("CPU timings exist despite failed equivalence gate")
    if cpu_env["status"].startswith("NOT_COMPLETED"):
        audit = read_csv(RESULTS / "historical_python_equivalence_audit.csv")
        if len(audit) != 36:
            failures.append(f"historical Python audit row count {len(audit)} != 36")
        if sum(row.get("pred_match") == "false" for row in audit) != 2:
            failures.append("historical Python prediction divergence is misreported")
        if sum(row.get("mem_match") == "false" for row in audit) != 22:
            failures.append("historical Python membrane divergence is misreported")
    if cpu_env["status"] == "COMPLETED":
        if len(cpu_rows) != 360 or len(e2e_rows) != 360:
            failures.append(f"Python measured rows kernel={len(cpu_rows)} end_to_end={len(e2e_rows)}, expected 360 each")
        check_repetitions(cpu_rows, "Python kernel", failures)
        check_repetitions(e2e_rows, "Python end-to-end", failures)
        for row in cpu_rows + e2e_rows:
            if row.get("output_match") not in ("1", "true"):
                failures.append(f"Python output mismatch: {row.get('case_id')}")
        equivalence = read_csv(RESULTS / "python_equivalence_gate.csv")
        if len(equivalence) != 36 or any(row.get("pred_match") != "true" or row.get("mem_match") != "true" for row in equivalence):
            failures.append("Python 36-case equivalence gate incomplete or mismatched")

    cpp_build = BENCH / "tools/cpp/cpp_build_environment.json"
    cpp_rows = read_csv(RESULTS / "cpu_cpp_kernel_runs.csv") if (RESULTS / "cpu_cpp_kernel_runs.csv").exists() else []
    if cpp_build.exists() and json.loads(cpp_build.read_text(encoding="utf-8"))["status"] == "BUILT":
        if len(cpp_rows) != 360:
            failures.append(f"C++ measured row count {len(cpp_rows)} != 360")
        check_repetitions(cpp_rows, "C++ kernel", failures)
        for row in cpp_rows:
            if row.get("output_match") != "true":
                failures.append(f"C++ output mismatch: {row.get('case_id')}")

    state = json.loads((RESULTS / "repository_start_state.json").read_text(encoding="utf-8"))
    dataset = RESULTS / "benchmark_dataset_manifest.csv"
    if digest(dataset) != state["dataset_manifest_sha256"]:
        failures.append("dataset manifest hash mismatch")
    for row in read_csv(dataset):
        path = REPO / row["path"]
        if not path.exists() or digest(path) != row["sha256"]:
            failures.append(f"benchmark input changed: {row['case_id']}")

    limitation = (REPORTS / "BENCHMARK_LIMITATIONS.md").read_text(encoding="utf-8")
    if "scope" not in limitation.lower() or "speedup" not in limitation.lower():
        failures.append("latency-scope warning missing")

    if failures:
        print("BENCHMARK_INTEGRITY_FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("BENCHMARK_INTEGRITY_PASS")
    print("- locked artifacts unchanged")
    print("- RTL 36/36 canonical cycle rows valid")
    print("- existing board functional audit 36/36 valid")
    print("- pending board values are nonnumeric")
    print("- no incompatible-scope speedup or fabricated power")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
