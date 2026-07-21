#!/usr/bin/env python3
"""Build the integrated metric registry only from pinned component evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DIGITAL_COMMIT = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
BENCHMARK_COMMIT = "d44e67517650f1f95ca67b93c2788f41e99f1a5e"
XMODEL_COMMIT = "4756a5086023547328ef44fd5fd87da3c250dc39"
MATLAB_COMMIT = "907f7e1f081a9d6a5703a32095d962143315a192"
LTSPICE_HANDOFF = "INTEGRATED_LTSPICE_2026-07-19"


def read_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


def read_csv(rel: str):
    with (ROOT / rel).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def metric(value, unit, scope, evidence_type, evidence_path, repo, commit, owner, limitation, status="VERIFIED"):
    return {
        "value": value,
        "unit": unit,
        "scope": scope,
        "evidence_type": evidence_type,
        "evidence_path": evidence_path,
        "upstream_repository": repo,
        "upstream_commit": commit,
        "owner": owner,
        "limitation": limitation,
        "verification_status": status,
    }


def main() -> int:
    digital_path = "components/digital_accelerator/reports/final/final_metrics.json"
    d = read_json(digital_path)
    assert d["final_model_id"] == "structural_guarded_silent_af_1008710"
    assert d["final_test_chunk"] == {
        "correct": 29, "total": 36, "accuracy_percent": 80.56,
        "macro_f1_percent": 80.44, "balanced_accuracy_percent": 80.56,
        "class_recall_percent": {"NSR": 100.0, "CHF": 66.67, "ARR": 77.78, "AF": 77.78},
    }
    assert d["board_replay_36"]["pred_match_correct"] == 36
    assert d["board_replay_36"]["final_mem_match_correct"] == 36

    xmodel_compare_path = "components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv"
    xr = read_csv(xmodel_compare_path)
    assert len(xr) == 36
    assert {row["sample_gap_cycles"] for row in xr} == {"2"}
    assert all(row["pred_match"].lower() == "true" for row in xr)
    assert all(row["mem_match"].lower() == "true" for row in xr)
    assert all(row["input_sha256_match"].lower() == "true" for row in xr)

    xmodel_verification_path = "components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md"
    verification_text = (ROOT / xmodel_verification_path).read_text(encoding="utf-8-sig")
    if not re.search(r"1\.95\s*LSB", verification_text):
        raise RuntimeError("XMODEL mean RMS evidence not found")

    matlab_path = "components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv"
    mr = [row for row in read_csv(matlab_path) if row["record_name"] in {"NSR", "CHF", "ARR", "AF"}]
    assert len(mr) == 4
    assert all(float(row["clipping_ratio_percent"]) == 0.0 for row in mr)
    minimum_headroom = min(float(row["minimum_headroom_to_rail_V"]) for row in mr)

    ltspice_handoff_path = "validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv"
    lh = {row["metric"]: row for row in read_csv(ltspice_handoff_path)}
    expected_handoff = {
        "sample_count": 10000.0,
        "mae": 0.6445,
        "rms_error": 1.3020,
        "max_abs_error": 13.0,
        "zero_lag_correlation": 0.999518,
        "best_lag": 0.0,
        "clipping_count": 0.0,
        "within_5_lsb_coverage": 98.74,
        "within_10_lsb_coverage": 99.89,
    }
    for name, expected in expected_handoff.items():
        assert float(lh[name]["value"]) == expected

    ltspice_execution_path = "validation/afe_ltspice_xmodel_aligned/tables/xmodel_aligned_execution_manifest.csv"
    le = read_csv(ltspice_execution_path)
    assert len(le) == 35
    assert all(row["status"] == "EXECUTED" for row in le)
    assert all(row["fatal_pattern"] == "False" and row["warning_pattern"] == "False" for row in le)

    benchmark_comparison = read_csv("benchmarks/accelerator_benefit/results/cpu_fpga_comparison.csv")
    assert len(benchmark_comparison) == 1
    bc = benchmark_comparison[0]
    rtl_benchmark = read_json("benchmarks/accelerator_benefit/results/rtl_cycle_summary.json")
    board_benchmark_path = "benchmarks/accelerator_benefit/results/board_timing_summary.json"
    board_benchmark = read_json(board_benchmark_path)
    power_benchmark_path = "benchmarks/accelerator_benefit/results/power_summary.json"
    power_benchmark = read_json(power_benchmark_path)
    activity_power_path = "benchmarks/accelerator_benefit/power/results/activity_power_summary.json"
    activity_power = read_json(activity_power_path)
    burst_activity = activity_power["groups"]["baseline:burst_full_record"]
    streaming_activity = activity_power["groups"]["baseline:streaming_1ksps_prefix"]
    clock_enable_path = "benchmarks/accelerator_benefit/power/results/clock_enable_summary.json"
    clock_enable = read_json(clock_enable_path)
    power_energy = read_csv("benchmarks/accelerator_benefit/results/power_energy_summary.csv")
    pure_rtl_1mhz_power = power_benchmark["scopes"]["pure_rtl_1mhz"]
    pure_rtl_power = power_benchmark["scopes"]["pure_rtl_100mhz"]
    system_power = power_benchmark["scopes"]["microblaze_system"]
    pure_rtl_energy = next(row for row in power_energy if row["implementation"] == "Pure RTL accelerator, 100 MHz core")
    system_energy = next(row for row in power_energy if row["implementation"] == "MicroBlaze integrated FPGA system")
    assert float(bc["cpu_latency_ms"]) == 1777.6998
    assert float(bc["fpga_latency_ms"]) == 54.0126
    assert round(float(bc["ratio_cpu_over_fpga"]), 6) == 32.912687
    assert rtl_benchmark["sample_gap_cycles"] == 2
    assert rtl_benchmark["active_total_cycles"]["median"] == 3601290
    assert board_benchmark["evidence_class"] == "MEASURED_COUNTERS_AND_DERIVED_ACTIVE_CYCLES"
    assert board_benchmark["cases_completed"] == 36
    assert board_benchmark["board_golden_final_pred"] == "36/36"
    assert board_benchmark["board_golden_final_membrane_values"] == "144/144"
    assert power_benchmark["evidence_class"] == "ESTIMATED"
    assert power_benchmark["physical_board_power_measured"] is False

    dr = "https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier"
    xr_name = "https://github.com/Hwan-22/ECG-SoC"
    mr_name = "https://github.com/ferocious-kiwi/ECG-SoC-MATLAB-AFE-ADC-Prevalidation"
    integrated_repo = "https://github.com/Sheep-gun/ECG-SoC-Integrated"
    metrics = {
        "schema_version": 1,
        "project_identity": "Holter-oriented long-window, multi-timescale, SNN-inspired ECG four-class classification accelerator IP",
        "metrics": {
            "locked_model_id": metric(d["final_model_id"], "identifier", "locked digital classifier", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "SNN-inspired event/state model; not a trained deep SNN claim"),
            "train_accuracy": metric(d["train"]["accuracy_percent"], "percent", f"{d['train']['correct']}/{d['train']['total']} train chunks", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "training fit; not held-out generalization"),
            "validation_accuracy": metric(d["validation"]["accuracy_percent"], "percent", f"{d['validation']['correct']}/{d['validation']['total']} validation chunks", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "model-selection split only; must not be promoted as final generalization"),
            "final_test_chunk_accuracy": metric(d["final_test_chunk"]["accuracy_percent"], "percent", "29/36 locked final-test 30-minute chunks", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "public-dataset engineering result; database-class confounding remains"),
            "final_test_chunk_macro_f1": metric(d["final_test_chunk"]["macro_f1_percent"], "percent", "36 locked final-test 30-minute chunks", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "public-dataset engineering result; class sample counts are limited"),
            "final_test_record_majority_accuracy": metric(d["final_test_record_majority"]["accuracy_percent"], "percent", "16/19 final-test source records after chunk-majority aggregation", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "aggregation result; not an independent second test"),
            "final_test_record_majority_macro_f1": metric(d["final_test_record_majority"]["macro_f1_percent"], "percent", "19 final-test source records", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "record-majority aggregation on the same locked final-test partition"),
            "final_test_evaluation_count": metric(d["test_evaluation_count"], "count", "locked final-test protocol", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "repository-declared protocol evidence"),
            "test_used_for_selection": metric(d["test_used_for_selection"], "boolean", "locked final-test protocol", "JSON", digital_path, dr, DIGITAL_COMMIT, "양건", "repository-declared protocol evidence"),
            "pure_rtl_lut": metric(d["pure_rtl_vivado"]["lut"], "LUT", "locked pure RTL implemented design", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "locked implementation authority; power reroute used 9749 LUT"),
            "pure_rtl_ff": metric(d["pure_rtl_vivado"]["ff"], "FF", "locked pure RTL implemented design", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "locked implementation authority; power reroute used 5045 FF"),
            "pure_rtl_bram": metric(d["pure_rtl_vivado"]["bram"], "BRAM", "locked pure RTL implemented design", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "resource count, not benchmark performance"),
            "pure_rtl_dsp": metric(d["pure_rtl_vivado"]["dsp"], "DSP", "locked pure RTL implemented design", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "resource count, not benchmark performance"),
            "pure_rtl_wns": metric(d["pure_rtl_vivado"]["wns_ns"], "ns", "locked pure RTL implementation timing closure", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "positive WNS under recorded constraints; power reroute WNS was 8.146 ns"),
            "microblaze_system_lut": metric(d["microblaze_full_replay_system"]["lut"], "LUT", "MicroBlaze full-replay system", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "whole-system resource, not pure accelerator resource"),
            "microblaze_system_ff": metric(d["microblaze_full_replay_system"]["slice_reg"], "slice register", "MicroBlaze full-replay system", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "whole-system resource"),
            "microblaze_system_bram": metric(d["microblaze_full_replay_system"]["bram"], "BRAM", "MicroBlaze full-replay system", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "whole-system resource"),
            "microblaze_system_dsp": metric(d["microblaze_full_replay_system"]["dsp"], "DSP", "MicroBlaze full-replay system", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "whole-system resource"),
            "microblaze_system_setup_wns": metric(d["microblaze_full_replay_system"]["setup_wns_ns"], "ns", "MicroBlaze full-replay system timing closure", "Vivado-derived JSON summary", digital_path, dr, DIGITAL_COMMIT, "양건", "positive WNS under recorded constraints; not board latency"),
            "board_final_pred_equivalence": metric("36/36", "cases", "FPGA board replay vs full-top XSim expected output", "board batch JSON", "components/digital_accelerator/reports/final/board_replay_36_batch_summary.json", dr, DIGITAL_COMMIT, "양건", "functional equivalence, not classification accuracy"),
            "board_final_mem_equivalence": metric("36/36", "cases", "FPGA board replay vs full-top XSim expected membrane", "board batch JSON", "components/digital_accelerator/reports/final/board_replay_36_batch_summary.json", dr, DIGITAL_COMMIT, "양건", "functional equivalence, not classification accuracy"),
            "board_label_accuracy": metric("29/36", "cases", "board outputs compared with locked final-test labels", "board batch JSON", "components/digital_accelerator/reports/final/board_replay_36_batch_summary.json", dr, DIGITAL_COMMIT, "양건", "same classification result as locked final-test chunks"),
            "board_active_core_latency_median": metric(board_benchmark["core_active_latency_ms"]["median"], "ms", "profile total minus input-wait hardware counters", "derived from measured board counters", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "core scope; depends on locked RTL input-wait semantics"),
            "board_active_core_cycles": metric(board_benchmark["core_active_cycles"]["median"], "cycles", "profile total minus input-wait hardware counters", "derived from measured board counters", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "identical in 36/36 board cases and XSim cross-check"),
            "board_active_core_throughput_median": metric(board_benchmark["core_active_throughput_samples_per_s"]["median"], "samples/s", "1,800,000 samples divided by active-core latency", "derived from measured board counters", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "stored-data active-core scope; live decision still needs 30 minutes"),
            "board_uart_paced_interval_median": metric(board_benchmark["uart_paced_transaction_counter_interval_ms"]["median"], "ms", "raw start-to-final-decision counter including input starvation", "measured board timing JSON", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "transport diagnostic only; not integrated-system compute latency"),
            "pure_rtl_estimated_power": metric(burst_activity["accelerator_plus_device_static_power_w"]["median"], "W", "100 MHz accelerator hierarchy dynamic plus allocated FPGA device static under four-class real-ECG burst SAIF", "post-implementation real-ECG SAIF Vivado estimate", activity_power_path, dr, BENCHMARK_COMMIT, "양건", "about 12 percent routed-net SAIF match; unmatched nets vectorless; not physical board input power"),
            "pure_rtl_100mhz_dynamic_power": metric(burst_activity["accelerator_hierarchy_dynamic_power_w"]["median"], "W", "100 MHz accelerator hierarchy under four-class real-ECG burst SAIF", "post-implementation real-ECG SAIF Vivado estimate", activity_power_path, dr, BENCHMARK_COMMIT, "양건", "accelerator hierarchy dynamic only; active dynamic energy is derived separately"),
            "pure_rtl_100mhz_device_static_power": metric(pure_rtl_power["device_static_power_w"], "W", "pure RTL accelerator at 100 MHz", "post-implementation vectorless Vivado estimate", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "device-static component of Total On-Chip Power"),
            "pure_rtl_1ksps_estimated_power": metric(streaming_activity["accelerator_plus_device_static_power_w"]["median"], "W", "literal 1 kS/s 100-sample real-ECG prefix; accelerator hierarchy dynamic plus allocated FPGA static", "post-implementation real-ECG SAIF Vivado estimate", activity_power_path, dr, BENCHMARK_COMMIT, "양건", "100-sample prefix rather than a full 30-minute trace; about 12 percent routed-net match"),
            "pure_rtl_clock_enable_coverage": metric(clock_enable["slice_registers_percent_gated"], "percent", "power_opt_design slice registers with user or tool gating", "Vivado power optimization report", clock_enable_path, dr, BENCHMARK_COMMIT, "양건", "gating coverage is implementation evidence; it did not materially change median power at 1 mW report resolution"),
            "pure_rtl_1mhz_estimated_power": metric(pure_rtl_1mhz_power["total_on_chip_power_w"], "W", "legacy low-frequency pure RTL implementation at 1 MHz core", "post-implementation vectorless Vivado estimate", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "power-only operating point; must not be multiplied by the 100 MHz active latency"),
            "microblaze_system_estimated_power": metric(system_power["total_on_chip_power_w"], "W", "MicroBlaze integrated FPGA system", "post-implementation vectorless Vivado estimate", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "estimated on-chip power; not physical board input power"),
            "pure_rtl_power_reroute_lut": metric(pure_rtl_power["utilization"]["lut"], "LUT", "100 MHz Pure RTL power-report implementation", "post-route Vivado power summary", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "direct 100 MHz wrapper implementation; resource values belong to this route"),
            "pure_rtl_power_reroute_ff": metric(pure_rtl_power["utilization"]["flip_flop"], "FF", "100 MHz Pure RTL power-report implementation", "post-route Vivado power summary", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "direct 100 MHz wrapper implementation; resource values belong to this route"),
            "pure_rtl_power_reroute_wns": metric(pure_rtl_power["timing"]["wns_ns"], "ns", "100 MHz Pure RTL power-report implementation", "post-route Vivado power summary", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "timing MET at 100 MHz; WNS is timing evidence, not processing latency"),
            "xmodel_emulator_mean_rms": metric(1.95, "LSB", "36 representative 60-second segments; emulator vs Questa/XMODEL after settling", "verification report", xmodel_verification_path, xr_name, XMODEL_COMMIT, "이수환", "model-to-model waveform agreement; max local deviations and solver differences remain"),
            "afe_input_sha256_identity": metric("36/36", "chunks", "AFE-generated final-test chunks vs digital board-replay inputs", "CSV row verification", xmodel_compare_path, xr_name, XMODEL_COMMIT, "이수환", "proves byte identity only, not label correctness"),
            "canonical_sample_gap_cycles": metric(2, "cycles", "board-facing full-top XSim integration cadence", "CSV row verification", xmodel_compare_path, xr_name, XMODEL_COMMIT, "이수환", "canonical integration condition; noncanonical debug cadence excluded"),
            "afe_to_rtl_final_pred_equivalence": metric("36/36", "chunks", "AFE-generated chunks at canonical cadence vs digital golden", "CSV row verification", xmodel_compare_path, xr_name, XMODEL_COMMIT, "이수환", "functional reproduction, not 100% classification accuracy"),
            "afe_to_rtl_final_mem_equivalence": metric("36/36", "chunks", "AFE-generated chunks at canonical cadence vs digital golden", "CSV row verification", xmodel_compare_path, xr_name, XMODEL_COMMIT, "이수환", "functional reproduction, not clinical validation"),
            "matlab_representative_clipping_ratio": metric(0.0, "percent", "NSR/CHF/ARR/AF representative 60-second nominal MATLAB records", "CSV aggregate", matlab_path, mr_name, MATLAB_COMMIT, "서민우", "nominal model-based pre-validation; not physical measurement"),
            "matlab_minimum_representative_headroom": metric(round(minimum_headroom, 12), "V", "minimum across NSR/CHF/ARR/AF representative nominal records", "CSV aggregate", matlab_path, mr_name, MATLAB_COMMIT, "서민우", "nominal MATLAB chain and selected representative records only"),
            "ltspice_execution_count": metric(35, "runs", "XMODEL-aligned LTspice nominal and stress regression", "execution manifest", ltspice_execution_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "LTspice behavioral op-amp implementation; not transistor-level, PCB, or silicon measurement"),
            "ltspice_xmodel_adc_sample_count": metric(10000, "samples", "same 10-second patient100 input at 1 kSPS", "CSV team handoff", ltspice_handoff_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "team-provided cross-tool comparison; regenerated raw waveforms are intentionally excluded because of size"),
            "ltspice_xmodel_adc_mae": metric(0.6445, "LSB", "LTspice S/H minus XMODEL over the same 10-second, 10,000-sample input", "CSV team handoff", ltspice_handoff_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "model-to-model agreement; not physical ADC error"),
            "ltspice_xmodel_adc_rms": metric(1.3020, "LSB", "LTspice S/H minus XMODEL over the same 10-second, 10,000-sample input", "CSV team handoff", ltspice_handoff_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "maximum local deviation is 13 LSB and is concentrated near fast ECG edges"),
            "ltspice_xmodel_adc_correlation": metric(0.999518, "ratio", "zero-lag LTspice/XMODEL ADC-code correlation over 10,000 samples", "CSV team handoff", ltspice_handoff_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "correlation alone does not establish sample-wise identity"),
            "ltspice_xmodel_within_5_lsb": metric(98.74, "percent", "absolute LTspice/XMODEL code error within 5 LSB over 10,000 samples", "CSV team handoff", ltspice_handoff_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "engineering tolerance coverage, not exact bit identity"),
            "ltspice_xmodel_within_10_lsb": metric(99.89, "percent", "absolute LTspice/XMODEL code error within 10 LSB over 10,000 samples", "CSV team handoff", ltspice_handoff_path, integrated_repo, LTSPICE_HANDOFF, "이수환", "11 samples exceed 10 LSB; maximum absolute error is 13 LSB"),
            "signed_stream_width": metric(12, "bits", "MATLAB/LTspice/XMODEL-to-digital interface", "component contract", "components/digital_accelerator/reports/final/digital_input_contract.md", dr, DIGITAL_COMMIT, "양건", "two's-complement signed digital handoff"),
            "signed_stream_sample_rate": metric(1000, "samples/s", "canonical ECG stream contract", "component contract", "components/digital_accelerator/reports/final/digital_input_contract.md", dr, DIGITAL_COMMIT, "양건", "input stream convention, not accelerator throughput"),
            "snapshot_duration": metric(60, "s", "Snapshot Readout interval", "locked architecture report", "components/digital_accelerator/FINAL_REPORT_KR.md", dr, DIGITAL_COMMIT, "양건", "architecture time scale at 1 kSPS"),
            "final_membrane_snapshots": metric(30, "snapshots", "Final Membrane accumulation", "locked architecture report", "components/digital_accelerator/FINAL_REPORT_KR.md", dr, DIGITAL_COMMIT, "양건", "30-minute common public-data window constrained by MIT-BIH Arrhythmia half-hour excerpts; not equivalent to 24-hour Holter validation"),
            "raw_input_window_samples": metric(1800000, "samples", "one 30-minute final-decision input at 1 kSPS", "interface and top-level RTL parameters", "components/digital_accelerator/rtl/snn_ecg_30min_final_top.v", dr, DIGITAL_COMMIT, "양건", "input-window size, not stored runtime memory"),
            "avoided_full_raw_input_window_bits": metric(21600000, "bits", "1800000 signed 12-bit samples", "derived arithmetic from verified interface/window", "docs/STREAMING_STATE_MEMORY_KR.md", "INTEGRATED", "INTEGRATED", "양건", "avoided full raw-input window storage; not exact synthesized memory saving", "VERIFIED_DERIVED"),
            "avoided_full_raw_input_window_bytes": metric(2700000, "bytes decimal", "21600000 bits divided by 8", "derived arithmetic from verified interface/window", "docs/STREAMING_STATE_MEMORY_KR.md", "INTEGRATED", "INTEGRATED", "양건", "approximately 2.7 MB decimal; not MicroBlaze runtime memory", "VERIFIED_DERIVED"),
        },
        "benchmark": {
            "status": "IMPORTED_VERIFIED_ACTIVE_CORE_AND_VIVADO_POWER",
            "upstream_commit": BENCHMARK_COMMIT,
            "cpu_baseline": "single-thread hand-written transaction-level Exact C++",
            "cpu_kernel_latency_ms": float(bc["cpu_latency_ms"]),
            "cpu_end_to_end_latency_ms": 2007.549250,
            "active_core_cycles": board_benchmark["core_active_cycles"]["median"],
            "active_core_latency_ms": board_benchmark["core_active_latency_ms"]["median"],
            "active_core_throughput_samples_per_s": board_benchmark["core_active_throughput_samples_per_s"]["median"],
            "active_core_realtime_margin_vs_1ksps": board_benchmark["core_active_realtime_margin_vs_1ksps"]["median"],
            "exact_cpp_to_active_core_speedup": float(bc["cpu_latency_ms"]) / board_benchmark["core_active_latency_ms"]["median"],
            "uart_paced_raw_interval_ms": board_benchmark["uart_paced_transaction_counter_interval_ms"]["median"],
            "integrated_system_compute_latency_ms": None,
            "exact_cpp_to_integrated_system_speedup": None,
            "legacy_gap_inclusive_rtl_latency_ms": float(bc["fpga_latency_ms"]),
            "legacy_gap_inclusive_speedup_estimate": float(bc["ratio_cpu_over_fpga"]),
            "estimated_power_w": burst_activity["accelerator_plus_device_static_power_w"]["median"],
            "estimated_pure_rtl_power_w": burst_activity["accelerator_plus_device_static_power_w"]["median"],
            "estimated_pure_rtl_100mhz_total_power_w": burst_activity["accelerator_plus_device_static_power_w"]["median"],
            "estimated_pure_rtl_100mhz_dynamic_power_w": burst_activity["accelerator_hierarchy_dynamic_power_w"]["median"],
            "estimated_pure_rtl_100mhz_device_static_power_w": pure_rtl_power["device_static_power_w"],
            "estimated_pure_rtl_literal_1ksps_power_w": streaming_activity["accelerator_plus_device_static_power_w"]["median"],
            "clock_enable_coverage_percent": clock_enable["slice_registers_percent_gated"],
            "estimated_pure_rtl_1mhz_power_w": pure_rtl_1mhz_power["total_on_chip_power_w"],
            "estimated_system_power_w": system_power["total_on_chip_power_w"],
            "measured_board_power_w": None,
            "estimated_energy_per_decision_j": float(pure_rtl_energy["energy_per_decision_j"]),
            "derived_pure_rtl_energy_per_decision_j": float(pure_rtl_energy["energy_per_decision_j"]),
            "derived_pure_rtl_active_dynamic_energy_per_decision_j": float(pure_rtl_energy["active_dynamic_energy_per_decision_j"]),
            "derived_system_energy_per_decision_j": None,
            "legacy_gap_inclusive_pure_rtl_energy_per_decision_j": None,
            "legacy_1mhz_power_energy_status": "NOT_DERIVED_CLOCK_MISMATCH",
            "measured_energy_per_decision_j": None,
            "board_timing_status": "MEASURED_COUNTERS_DERIVED_ACTIVE_CORE",
            "integrated_system_timing_status": "NOT_MEASURED_REQUIRES_PRELOAD_AND_INDEPENDENT_TIMER",
            "board_power_status": "NOT_MEASURED",
            "power_estimate_status": "POST_IMPLEMENTATION_REAL_ECG_SAIF_ESTIMATED_MEDIUM_CONFIDENCE",
            "scope_limitation": "active-core latency subtracts RUN-state input starvation from measured counters; the 100 MHz latency is combined with a four-class real-ECG burst-SAIF accelerator estimate with about 12 percent routed-net match; unmatched nets remain vectorless; the 1 MHz 0.099 W result is power-only; integrated-system latency and physical board input power are unmeasured",
        },
    }
    out = ROOT / "source_of_truth" / "global_metrics.yaml"
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} with {len(metrics['metrics'])} verified metrics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
