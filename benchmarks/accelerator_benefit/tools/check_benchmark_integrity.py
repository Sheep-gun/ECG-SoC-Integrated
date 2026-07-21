#!/usr/bin/env python3
"""Fail closed on benchmark scope, equivalence, and evidence violations."""

from __future__ import annotations

import csv
import hashlib
import json
import re
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
        "benchmarks/accelerator_benefit/exact_cpp/",
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
        if (
            int(row.get("active_total_cycles", "0")) != 3_601_290
            or int(row.get("active_run_cycles", "0")) != 3_599_970
            or int(row.get("non_run_overhead_cycles", "0")) != 1_320
            or row.get("active_total_latency_ms") != "36.012900000"
        ):
            failures.append(f"{case}: RTL active-cycle invariant failed")

    board = read_csv(RESULTS / "existing_board_functional_audit.csv")
    if len(board) != 36:
        failures.append(f"board audit row count {len(board)} != 36")
    for row in board:
        if row.get("transcript_exists") != "true" or row.get("final_pred_match") != "1" or row.get("final_mem_match") != "1":
            failures.append(f"{row.get('case_id')}: board evidence misreported")
        if row.get("timing_measurement_present") != "false":
            failures.append(f"{row.get('case_id')}: old transcript incorrectly used as timing")

    summary = read_csv(RESULTS / "accelerator_benefit_summary.csv")
    if len(summary) < 8:
        failures.append(f"comparison row count {len(summary)} < 8")
    summary_by_name = {row.get("implementation"): row for row in summary}
    if "Exact C++ native CPU kernel" not in summary_by_name:
        failures.append("Exact C++ native CPU baseline row missing")
    verilator_row = summary_by_name.get("Verilator-generated RTL simulation")
    if not verilator_row or verilator_row.get("speedup_vs_python_kernel") != "N/A":
        failures.append("Verilator runtime is missing or incorrectly treated as a CPU speedup baseline")
    for row in summary:
        if not row.get("evidence_path"):
            failures.append(f"{row.get('implementation')}: missing evidence path")
        speedup = row.get("speedup_vs_python_kernel")
        compatible_speedup = row.get("implementation") in {
            "Python integer kernel", "Exact C++ native CPU kernel",
            "Pure RTL XSim active-cycle cross-check",
            "FPGA board accelerator active-cycle latency",
        }
        if speedup not in ("", "N/A") and not compatible_speedup:
            failures.append(f"{row.get('implementation')}: incompatible-scope speedup present")
    active_row = summary_by_name.get("FPGA board accelerator active-cycle latency")
    if not active_row or active_row.get("status") != "DERIVED":
        failures.append("FPGA board active-cycle row missing or mislabeled")
    elif active_row.get("speedup_vs_exact_cpp_kernel") != "49.362862":
        failures.append("FPGA active-core Exact C++ speedup mismatch")
    uart_row = summary_by_name.get("FPGA board UART-paced transaction diagnostic")
    if not uart_row or uart_row.get("status") != "MEASURED":
        failures.append("UART-paced diagnostic row missing or mislabeled")
    elif uart_row.get("speedup_vs_exact_cpp_kernel") != "N/A" or uart_row.get("energy_per_decision_j") != "N/A":
        failures.append("UART-paced interval incorrectly used for speedup or energy")

    power = read_csv(RESULTS / "power_energy_summary.csv")
    power_by_name = {row["implementation"]: row for row in power}
    legacy_power = power_by_name.get("Pure RTL accelerator, 1 MHz core", {})
    if (
        legacy_power.get("core_clock_mhz") != "1.000000"
        or legacy_power.get("power_w") != "0.099000"
        or legacy_power.get("energy_per_decision_j") != "NOT_DERIVED"
        or legacy_power.get("energy_class") != "NOT_DERIVED_CLOCK_MISMATCH"
    ):
        failures.append("1 MHz Pure RTL power is missing or incorrectly combined with 100 MHz latency")
    matched_power = power_by_name.get("Pure RTL accelerator, 100 MHz core", {})
    if (
        matched_power.get("core_clock_mhz") != "100.000000"
        or matched_power.get("power_w") != "0.149500"
        or matched_power.get("dynamic_power_w") != "0.052500"
        or matched_power.get("device_static_power_w") != "0.097000"
        or matched_power.get("energy_per_decision_j") != "0.005383928550"
        or matched_power.get("active_dynamic_energy_per_decision_j") != "0.001890677250"
        or matched_power.get("energy_class") != "DERIVED_ESTIMATE"
    ):
        failures.append("100 MHz Pure RTL power or clock-matched energy is invalid")
    for row in power:
        if row["implementation"] == "MicroBlaze integrated FPGA system" and (
            row.get("power_class") != "ESTIMATED"
            or row.get("energy_class") != "NOT_MEASURED"
            or row.get("energy_per_decision_j") != "NOT_MEASURED"
        ):
            failures.append("integrated system energy incorrectly inferred")
        if row["implementation"] == "Physical FPGA board":
            if (
                row.get("power_class") != "NOT_MEASURED"
                or row.get("energy_class") != "NOT_MEASURED"
                or row["power_w"] != "NOT_MEASURED"
            ):
                failures.append("board power fabricated or zero-filled")
        if row["implementation"] == "CPU" and row.get("power_class") != "N/A":
            failures.append("CPU energy reported without counter")

    board_build_status = json.loads((BENCH / "board/build/build_status.json").read_text(encoding="utf-8"))
    if board_build_status.get("status") == "built":
        built_elf = BENCH / "board/build/snn_ecg_mb_full_replay_benchmark.elf"
        if not built_elf.exists() or digest(built_elf) != board_build_status.get("elf_sha256"):
            failures.append("instrumented board ELF missing or hash mismatch")

    measured_board = read_csv(BENCH / "board/board_timing_results.csv")
    if len(measured_board) != 36:
        failures.append(f"measured board timing row count {len(measured_board)} != 36")
    active_cycle_values: set[int] = set()
    for row in measured_board:
        case_id = row.get("case_id", "<unknown>")
        if (
            row.get("sample_count") != "1800000"
            or int(row.get("core_cycles", "0")) <= 0
            or int(row.get("system_cycles", "0")) <= 0
            or row.get("pred_match") != "1"
            or row.get("mem_match") != "1"
        ):
            failures.append(f"{case_id}: measured board timing acceptance failed")
        try:
            total = int(row.get("profile_total_cycles", "0"))
            run = int(row.get("profile_run_cycles", "0"))
            wait = int(row.get("profile_input_wait_cycles", "0"))
            active = int(row.get("core_active_cycles", "0"))
            run_active = int(row.get("core_run_active_cycles", "0"))
            non_run = int(row.get("non_run_overhead_cycles", "0"))
            active_cycle_values.add(active)
            if (
                total != int(row.get("core_cycles", "0"))
                or total != int(row.get("system_cycles", "0"))
                or int(row.get("profile_accepted_samples", "0")) != 1_800_000
                or active != total - wait
                or run_active != run - wait
                or non_run != total - run
                or active != 3_601_290
                or run_active != 3_599_970
                or non_run != 1_320
                or row.get("core_active_latency_ms") != "36.012900000"
            ):
                failures.append(f"{case_id}: active-cycle derivation failed")
        except ValueError:
            failures.append(f"{case_id}: active-cycle field is not numeric")
        transcript = BENCH / "board/future_run/transcripts" / f"{case_id}.txt"
        parsed_path = BENCH / "board/future_run/parsed" / f"{case_id}.json"
        if not parsed_path.exists():
            failures.append(f"{case_id}: measured parsed JSON missing")
        else:
            parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
            board_values = parsed.get("board") or {}
            if (
                parsed.get("status") != "completed"
                or parsed.get("board_internal_pass") is not True
                or board_values.get("total_samples") != 1_800_000
                or board_values.get("samples_received") != 1_800_000
                or board_values.get("samples_sent_to_ip") != 1_800_000
                or board_values.get("samples_accepted") != 1_800_000
                or board_values.get("samples_consumed") != 1_800_000
                or board_values.get("snapshot_count") != 30
                or board_values.get("decision_count") != 1
                or board_values.get("done") != 1
                or board_values.get("final_valid") != 1
            ):
                failures.append(f"{case_id}: parsed board invariants failed")
        if not transcript.exists():
            failures.append(f"{case_id}: measured transcript missing")
            continue
        text = transcript.read_text(encoding="utf-8", errors="replace")
        if len(re.findall(r"^BOARD_BENCH\s", text, re.MULTILINE)) != 1:
            failures.append(f"{case_id}: BOARD_BENCH count is not one")
        if text.count("SNN_ECG_FULL_REPLAY_BOARD_PASS") != 1:
            failures.append(f"{case_id}: board PASS count is not one")
    if active_cycle_values != {3_601_290}:
        failures.append(f"board active-cycle values are not invariant: {sorted(active_cycle_values)}")
    board_batch = json.loads((BENCH / "board/future_run/batch_summary.json").read_text(encoding="utf-8"))
    if (
        board_batch.get("status") != "completed"
        or board_batch.get("validation_result") != "pass"
        or board_batch.get("cases_completed") != 36
        or board_batch.get("cases_passed") != 36
        or board_batch.get("pred_match_correct") != 36
        or board_batch.get("final_mem_match_correct") != 36
        or board_batch.get("classification_correct") != 29
    ):
        failures.append("36-case board batch summary acceptance failed")
    timing_summary = json.loads((BENCH / "board/board_timing_summary.json").read_text(encoding="utf-8"))
    if (
        timing_summary.get("evidence_class") != "MEASURED_COUNTERS_AND_DERIVED_ACTIVE_CYCLES"
        or timing_summary.get("cases_completed") != 36
        or not 0 <= int(timing_summary.get("core_system_equal_cases", -1)) <= 36
        or float(timing_summary.get("core_active_cycles", {}).get("median", 0)) != 3_601_290
        or float(timing_summary.get("core_active_latency_ms", {}).get("median", 0)) != 36.0129
        or float(timing_summary.get("input_wait_latency_ms", {}).get("median", 0)) <= 0
        or timing_summary.get("xsim_active_cycle_crosscheck") != "36/36"
        or timing_summary.get("system_compute_latency_status") != "NOT_MEASURED_REQUIRES_PRELOAD_AND_INDEPENDENT_TIMER"
    ):
        failures.append("measured board timing summary invalid")

    power_summary = json.loads((BENCH / "power/results/power_summary.json").read_text(encoding="utf-8"))
    if power_summary.get("physical_board_power_measured") is not False:
        failures.append("physical board power incorrectly marked measured")
    scopes = power_summary.get("scopes", {})
    if set(scopes) != {"pure_rtl_1mhz", "pure_rtl_100mhz", "microblaze_system"}:
        failures.append("power summary scopes invalid")
    for name, scope in scopes.items():
        report = REPO / scope.get("raw_power_report", "")
        if (
            scope.get("evidence_class") != "ESTIMATED"
            or scope.get("implementation_status") != "routed"
            or float(scope.get("total_on_chip_power_w", 0)) <= 0
            or not report.exists()
            or digest(report) != scope.get("raw_power_report_sha256")
            or "vectorless" not in scope.get("activity_source", "").lower()
            or scope.get("timing", {}).get("status") != "MET"
        ):
            failures.append(f"{name}: power report evidence invalid")
    if (
        scopes.get("pure_rtl_1mhz", {}).get("core_clock_frequency_mhz") != 1.0
        or scopes.get("pure_rtl_1mhz", {}).get("total_on_chip_power_w") != 0.099
    ):
        failures.append("1 MHz Pure RTL operating point invalid")
    pure_100 = scopes.get("pure_rtl_100mhz", {})
    if (
        pure_100.get("core_clock_frequency_mhz") != 100.0
        or pure_100.get("total_on_chip_power_w") != 0.183
        or pure_100.get("dynamic_power_w") != 0.085
        or pure_100.get("device_static_power_w") != 0.097
        or pure_100.get("utilization") != {"lut": 9759, "flip_flop": 5049, "bram_tile": 0, "dsp": 0}
        or pure_100.get("timing", {}).get("wns_ns") != 0.035
    ):
        failures.append("100 MHz Pure RTL implementation metrics invalid")
    for artifact_key, hash_key in [
        ("utilization_report", "utilization_report_sha256"),
        ("timing_report", "timing_report_sha256"),
        ("environment_record", "environment_record_sha256"),
        ("build_manifest", "build_manifest_sha256"),
    ]:
        artifact = REPO / pure_100.get(artifact_key, "")
        if not artifact.exists() or digest(artifact) != pure_100.get(hash_key):
            failures.append(f"100 MHz Pure RTL {artifact_key} hash mismatch")
    build_manifest_path = REPO / pure_100.get("build_manifest", "")
    if build_manifest_path.exists():
        build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
        if (
            build_manifest.get("status") != "COMPLETED"
            or build_manifest.get("vivado_exit_code") != 0
            or build_manifest.get("timing_status") != "MET"
            or build_manifest.get("wns_ns") != 0.035
            or build_manifest.get("core_clock_mhz") != 100.0
        ):
            failures.append("100 MHz Pure RTL build manifest status invalid")
        artifact_entries = [build_manifest.get("source", {}), build_manifest.get("constraint", {}), build_manifest.get("script", {})]
        artifact_entries.extend(build_manifest.get("reports", {}).values())
        for entry in artifact_entries:
            artifact = REPO / entry.get("path", "")
            if not artifact.exists() or digest(artifact) != entry.get("sha256"):
                failures.append(f"100 MHz build-manifest artifact hash mismatch: {entry.get('path')}")

    invalid_mixed_energy = "0.003565277"
    for relative in [
        "benchmarks/accelerator_benefit/README.md",
        "benchmarks/accelerator_benefit/reports/ACCELERATOR_BENEFIT_KR.md",
        "benchmarks/accelerator_benefit/reports/ACCELERATOR_BENEFIT_EN.md",
        "benchmarks/accelerator_benefit/reports/POWER_ENERGY_METHODOLOGY.md",
        "benchmarks/accelerator_benefit/results/power_energy_summary.csv",
        "benchmarks/accelerator_benefit/results/accelerator_benefit_summary.csv",
    ]:
        if invalid_mixed_energy in (REPO / relative).read_text(encoding="utf-8"):
            failures.append(f"mixed-clock energy remains in final artifact: {relative}")

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

    exact_cpp = BENCH / "exact_cpp"
    native_raw = read_csv(exact_cpp / "results/exact_cpp_cpu_raw.csv")
    native_performance = json.loads((exact_cpp / "results/performance_integrity.json").read_text(encoding="utf-8"))
    native_post = json.loads((exact_cpp / "results/post_benchmark_equivalence.json").read_text(encoding="utf-8"))
    if native_performance.get("status") != "pass" or native_post.get("status") != "pass":
        failures.append("transaction-level Exact C++ package gate failed")
    if len(native_raw) != 720 or len({row.get("case_id") for row in native_raw}) != 36:
        failures.append(f"transaction-level Exact C++ rows/cases {len(native_raw)}/{len({row.get('case_id') for row in native_raw})}, expected 720/36")
    native_groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in native_raw:
        native_groups.setdefault((row.get("case_id", ""), row.get("mode", "")), []).append(row)
        if (
            row.get("output_exact") != "1"
            or row.get("samples") != "1800000"
            or row.get("accepted_samples") != "1800000"
            or row.get("snapshots") != "30"
            or row.get("decisions") != "1"
        ):
            failures.append(f"transaction-level Exact C++ invariant failed: {row.get('case_id')}/{row.get('mode')}/{row.get('repetition')}")
    if len(native_groups) != 72:
        failures.append(f"transaction-level Exact C++ case/mode group count {len(native_groups)} != 72")
    for (case_id, mode), mode_rows in native_groups.items():
        if len(mode_rows) != 10 or {row.get("repetition") for row in mode_rows} != {str(i) for i in range(1, 11)}:
            failures.append(f"transaction-level Exact C++ repetitions invalid: {case_id}/{mode}")
    native_comparison = read_csv(exact_cpp / "results/cpu_fpga_comparison.csv")
    if len(native_comparison) != 1 or native_comparison[0].get("ratio_cpu_over_fpga") != "32.912687040":
        failures.append("transaction-level Exact C++ FPGA-core comparison mismatch")

    state = json.loads((RESULTS / "repository_start_state.json").read_text(encoding="utf-8"))
    dataset = RESULTS / "benchmark_dataset_manifest.csv"
    if digest(dataset) != state["dataset_manifest_sha256"]:
        failures.append("dataset manifest hash mismatch")
    for row in read_csv(dataset):
        path = REPO / row["path"]
        if not path.exists() or digest(path) != row["sha256"]:
            failures.append(f"benchmark input changed: {row['case_id']}")

    activity_path = BENCH / "power/results/activity_power_summary.json"
    if activity_path.exists():
        activity = json.loads(activity_path.read_text(encoding="utf-8"))
        activity_rows = activity.get("records", [])
        expected_pairs = {
            (implementation, mode)
            for implementation in ("baseline", "power_opt")
            for mode in ("burst_full_record", "streaming_1ksps_prefix")
        }
        actual_pairs = {(row.get("implementation"), row.get("mode")) for row in activity_rows}
        if len(activity_rows) != 16 or actual_pairs != expected_pairs:
            failures.append(f"activity power records/pairs invalid: {len(activity_rows)} {sorted(actual_pairs)}")
        for row in activity_rows:
            report = REPO / row.get("raw_power_report", "")
            saif = REPO / row.get("saif", "")
            if (
                row.get("evidence_class") != "ESTIMATED"
                or row.get("power_estimation_confidence") != "Medium"
                or not str(row.get("design_nets_matched", "")).startswith("12%")
                or float(row.get("timing_wns_ns", -1)) < 0
                or not report.exists()
                or digest(report) != row.get("raw_power_report_sha256")
                or not saif.exists()
                or digest(saif) != row.get("saif_sha256")
            ):
                failures.append(f"activity power evidence invalid: {row.get('implementation')}/{row.get('case_id')}/{row.get('mode')}")
        if activity.get("physical_board_power_measured") is not False:
            failures.append("activity summary mislabels physical board power")

        ce = json.loads((BENCH / "power/results/clock_enable_summary.json").read_text(encoding="utf-8"))
        if (
            ce.get("functional_rtl_changed") is not False
            or ce.get("slice_registers_total") != 5044
            or ce.get("slice_registers_user_gated", 0) <= 0
            or ce.get("slice_registers_tool_gated", 0) <= 0
            or ce.get("slice_registers_percent_gated", 0) <= 0
        ):
            failures.append("clock-enable/power-opt evidence invalid")

        board_power = json.loads((BENCH / "power/results/board_measurement_availability.json").read_text(encoding="utf-8"))
        if board_power.get("physical_board_power_measured") is not False or board_power.get("external_power_meter_detected") is not False:
            failures.append("physical rail measurement boundary invalid")

        asic = json.loads((BENCH / "asic_handoff/asic_environment.json").read_text(encoding="utf-8"))
        if asic.get("status") != "BLOCKED_NO_PDK_OR_ASIC_TOOLCHAIN":
            failures.append("ASIC PPA blocker status invalid")

        wearable = json.loads((BENCH / "power/results/wearable_power_budget.json").read_text(encoding="utf-8"))
        if wearable.get("complete_wearable_budget_available") is not False:
            failures.append("incomplete wearable power budget incorrectly marked complete")

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
    print("- measured board counters and 36 raw transcripts accepted")
    print("- raw Vivado power reports and hashes accepted")
    print("- no fabricated physical-board power")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
