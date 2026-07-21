#!/usr/bin/env python3
"""Build the integrated metric registry only from pinned component evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DIGITAL_COMMIT = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
BENCHMARK_COMMIT = "46f90224fca0dea3a592049a5e14b97680d529e0"
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
    power_energy = read_csv("benchmarks/accelerator_benefit/results/power_energy_summary.csv")
    pure_rtl_power = power_benchmark["scopes"]["pure_rtl"]
    system_power = power_benchmark["scopes"]["microblaze_system"]
    pure_rtl_energy = next(row for row in power_energy if row["implementation"] == "Pure RTL accelerator")
    system_energy = next(row for row in power_energy if row["implementation"] == "MicroBlaze integrated FPGA system")
    assert float(bc["cpu_latency_ms"]) == 1777.6998
    assert float(bc["fpga_latency_ms"]) == 54.0126
    assert round(float(bc["ratio_cpu_over_fpga"]), 6) == 32.912687
    assert rtl_benchmark["sample_gap_cycles"] == 2 and rtl_benchmark["profile_total_cycles"] == 5401260
    assert board_benchmark["evidence_class"] == "MEASURED"
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
            "board_core_latency_median": metric(board_benchmark["core_latency_ms"]["median"], "ms", "accelerator last-decision hardware-counter interval", "measured board timing JSON", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "includes UART-paced input wait; not no-stall accelerator compute time"),
            "board_system_latency_median": metric(board_benchmark["system_latency_ms"]["median"], "ms", "full transaction hardware-counter interval", "measured board timing JSON", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "fixed XSA has no independent AXI Timer; equals core counter for all 36 cases"),
            "board_system_throughput_median": metric(board_benchmark["system_throughput_samples_per_s"]["median"], "samples/s", "1,800,000-sample hardware transaction", "measured board timing JSON", board_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "UART-paced host streaming is included"),
            "pure_rtl_estimated_power": metric(pure_rtl_power["total_on_chip_power_w"], "W", "pure RTL accelerator", "post-implementation vectorless Vivado estimate", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "estimated on-chip power; not physical board input power"),
            "microblaze_system_estimated_power": metric(system_power["total_on_chip_power_w"], "W", "MicroBlaze integrated FPGA system", "post-implementation vectorless Vivado estimate", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "estimated on-chip power; not physical board input power"),
            "pure_rtl_power_reroute_lut": metric(pure_rtl_power["utilization"]["lut"], "LUT", "Pure RTL power-report reroute", "post-route Vivado power summary", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "same RTL/part/clock; route differs slightly from locked canonical implementation"),
            "pure_rtl_power_reroute_ff": metric(pure_rtl_power["utilization"]["flip_flop"], "FF", "Pure RTL power-report reroute", "post-route Vivado power summary", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "same RTL/part/clock; route differs slightly from locked canonical implementation"),
            "pure_rtl_power_reroute_wns": metric(pure_rtl_power["timing"]["wns_ns"], "ns", "Pure RTL power-report reroute", "post-route Vivado power summary", power_benchmark_path, dr, BENCHMARK_COMMIT, "양건", "timing closure evidence; not processing latency"),
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
            "status": "IMPORTED_VERIFIED_BOARD_TIMING_AND_VIVADO_POWER",
            "upstream_commit": BENCHMARK_COMMIT,
            "cpu_baseline": "single-thread hand-written transaction-level Exact C++",
            "cpu_kernel_latency_ms": float(bc["cpu_latency_ms"]),
            "cpu_end_to_end_latency_ms": 2007.549250,
            "rtl_processing_latency_ms": float(bc["fpga_latency_ms"]),
            "rtl_throughput_samples_per_s": rtl_benchmark["throughput_samples_per_s"],
            "realtime_headroom": rtl_benchmark["realtime_margin_vs_1ksps"],
            "exact_cpp_to_rtl_speedup_estimate": float(bc["ratio_cpu_over_fpga"]),
            "board_core_latency_ms": board_benchmark["core_latency_ms"]["median"],
            "board_system_latency_ms": board_benchmark["system_latency_ms"]["median"],
            "board_system_throughput_samples_per_s": board_benchmark["system_throughput_samples_per_s"]["median"],
            "board_realtime_margin_vs_1ksps": board_benchmark["system_realtime_margin_vs_1ksps"]["median"],
            "exact_cpp_to_board_core_ratio": float(bc["cpu_latency_ms"]) / board_benchmark["core_latency_ms"]["median"],
            "exact_cpp_to_board_system_ratio": float(bc["cpu_latency_ms"]) / board_benchmark["system_latency_ms"]["median"],
            "estimated_power_w": pure_rtl_power["total_on_chip_power_w"],
            "estimated_pure_rtl_power_w": pure_rtl_power["total_on_chip_power_w"],
            "estimated_system_power_w": system_power["total_on_chip_power_w"],
            "measured_board_power_w": None,
            "estimated_energy_per_decision_j": float(pure_rtl_energy["energy_per_decision_j"]),
            "derived_pure_rtl_energy_per_decision_j": float(pure_rtl_energy["energy_per_decision_j"]),
            "derived_system_energy_per_decision_j": float(system_energy["energy_per_decision_j"]),
            "legacy_cycle_derived_pure_rtl_energy_per_decision_j": 0.0053472474,
            "measured_energy_per_decision_j": None,
            "board_timing_status": "MEASURED",
            "board_power_status": "NOT_MEASURED",
            "power_estimate_status": "POST_IMPLEMENTATION_VECTORLESS_ESTIMATED",
            "scope_limitation": "measured hardware counters include UART-paced input wait; Vivado power is an on-chip vectorless estimate; physical board input power was not measured",
        },
    }
    out = ROOT / "source_of_truth" / "global_metrics.yaml"
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} with {len(metrics['metrics'])} verified metrics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
