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
        if speedup not in ("", "N/A"):
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

    cpu_env = json.loads((RESULTS / "cpu_environment.json").read_text(encoding="utf-8"))
    cpu_rows = read_csv(RESULTS / "cpu_python_kernel_runs.csv")
    if cpu_env["status"].startswith("NOT_COMPLETED") and cpu_rows:
        failures.append("CPU timings exist despite failed equivalence gate")
    if not cpu_env["status"].startswith("NOT_COMPLETED"):
        for row in cpu_rows:
            if row.get("output_match") not in ("1", "true"):
                failures.append(f"Python output mismatch: {row.get('case_id')}")

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
