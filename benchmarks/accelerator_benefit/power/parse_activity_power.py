#!/usr/bin/env python3
"""Parse real-ECG SAIF post-route power reports and derive mode statistics."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
POWER = REPO / "benchmarks" / "accelerator_benefit" / "power"
RESULTS = POWER / "results"
MANIFEST = RESULTS / "activity" / "activity_manifest.json"
ACTIVITY_POWER = RESULTS / "activity_power"
OUT_JSON = RESULTS / "activity_power_summary.json"
OUT_CSV = RESULTS / "activity_power_summary.csv"
CE_JSON = RESULTS / "clock_enable_summary.json"
CE_CSV = RESULTS / "clock_enable_summary.csv"
ACTIVE_LATENCY_S = 0.0360129
RECORD_DURATION_S = 1800.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def required(pattern: str, text: str, name: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"cannot parse {name}")
    return match.group(1).strip()


def optional(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.lower()] = value
    return values


def numeric_power(pattern: str, text: str, name: str) -> float:
    return float(required(pattern, text, name))


def component_power(text: str, name: str) -> float | None:
    value = optional(rf"\|\s*{re.escape(name)}\s*\|\s*(<?[0-9.]+)", text)
    if value is None:
        return None
    return 0.0005 if value.startswith("<") else float(value)


def parse_record(
    implementation: str, record: dict[str, Any], report: Path, environment: Path, unmatched: Path, timing: Path
) -> dict[str, Any]:
    text = report.read_text(encoding="utf-8", errors="replace")
    env_values = env(environment)
    timing_text = timing.read_text(encoding="utf-8", errors="replace")
    wns_text = optional(r"WNS\(ns\).*?\n[-+|\s]*\n\s*\|?\s*([-0-9.]+)", timing_text)
    total = numeric_power(r"\| Total On-Chip Power \(W\)\s*\|\s*([0-9.]+)", text, "total power")
    dynamic = numeric_power(r"\| Dynamic \(W\)\s*\|\s*([0-9.]+)", text, "dynamic power")
    static = numeric_power(r"\| Device Static \(W\)\s*\|\s*([0-9.]+)", text, "static power")
    dut_dynamic_text = optional(r"\|\s+u_dut\s*\|\s*([0-9.]+)", text)
    dut_dynamic = float(dut_dynamic_text) if dut_dynamic_text is not None else dynamic
    accelerator_allocated_total = static + dut_dynamic
    mode = record["mode"]
    energy = None
    duty = None
    if mode == "burst_full_record":
        duty = ACTIVE_LATENCY_S / RECORD_DURATION_S
        energy = {
            "latency_evidence_class": "DERIVED",
            "active_latency_s": ACTIVE_LATENCY_S,
            "total_energy_per_decision_mj": total * ACTIVE_LATENCY_S * 1000.0,
            "dynamic_energy_per_decision_mj": dynamic * ACTIVE_LATENCY_S * 1000.0,
            "accelerator_allocated_energy_per_decision_mj": accelerator_allocated_total * ACTIVE_LATENCY_S * 1000.0,
            "accelerator_dynamic_energy_per_decision_mj": dut_dynamic * ACTIVE_LATENCY_S * 1000.0,
            "clock_gated_no_power_gating_average_power_w": static + dynamic * duty,
            "dynamic_duty_cycled_average_power_w": dynamic * duty,
            "ideal_full_power_gating_average_power_w": total * duty,
            "accelerator_clock_gated_no_power_gating_average_power_w": static + dut_dynamic * duty,
            "accelerator_dynamic_duty_cycled_average_power_w": dut_dynamic * duty,
            "accelerator_ideal_full_power_gating_average_power_w": accelerator_allocated_total * duty,
            "record_period_s": RECORD_DURATION_S,
            "active_duty_fraction": duty,
        }
    return {
        "implementation": implementation,
        "case_id": record["case_id"],
        "class_label_internal": record["class_label_internal"],
        "class_label_report": record["class_label_report"],
        "mode": mode,
        "sample_count": record["sample_count"],
        "sample_gap_cycles": record["sample_gap_cycles"],
        "literal_sample_rate_hz": record["literal_sample_rate_hz"],
        "saif_duration_s": record["saif_duration_s"],
        "functional_final_checked": record["functional_final_checked"],
        "evidence_class": "ESTIMATED",
        "estimate_description": "Post-implementation real-ECG SAIF-based Vivado power estimate",
        "vivado_version": required(r"\| Tool Version\s*:\s*(.+)", text, "Vivado version"),
        "fpga_part": required(r"\| Device\s*:\s*(.+)", text, "device"),
        "design_top": required(r"\| Design\s*:\s*(.+)", text, "design"),
        "implementation_status": required(r"\| Design State\s*:\s*(.+)", text, "design state"),
        "clock_frequency_mhz": 100.0,
        "total_on_chip_power_w": total,
        "dynamic_power_w": dynamic,
        "device_static_power_w": static,
        "accelerator_hierarchy_dynamic_power_w": dut_dynamic,
        "accelerator_plus_device_static_power_w": accelerator_allocated_total,
        "component_power_w": {
            "clocks": component_power(text, "Clocks"),
            "slice_logic": component_power(text, "Slice Logic"),
            "signals": component_power(text, "Signals"),
            "io": component_power(text, "I/O"),
        },
        "power_estimation_confidence": required(r"\| Confidence Level\s*\|\s*([^|]+)", text, "confidence"),
        "junction_temperature_c": numeric_power(r"\| Junction Temperature \(C\)\s*\|\s*([0-9.]+)", text, "junction temperature"),
        "simulation_activity_file": required(r"\| Simulation Activity File\s*\|\s*([^|]+)", text, "SAIF path"),
        "design_nets_matched": required(r"\| Design Nets Matched\s*\|\s*([^|]+)", text, "matched nets"),
        "activity_source": env_values.get("activity_source"),
        "saif_strip_path": env_values.get("saif_strip_path"),
        "reset_policy": env_values.get("reset_policy"),
        "register_primitives": int(env_values.get("register_primitives", "0")),
        "register_ce_pins": int(env_values.get("register_ce_pins", "0")),
        "register_ce_pins_with_driven_net": int(env_values.get("register_ce_pins_with_driven_net", "0")),
        "timing_wns_ns": float(wns_text) if wns_text is not None else None,
        "energy": energy,
        "raw_power_report": rel(report),
        "raw_power_report_sha256": sha256(report),
        "saif": record["saif"],
        "saif_sha256": record["saif_sha256"],
        "saif_unmatched_report": rel(unmatched),
        "saif_unmatched_report_sha256": sha256(unmatched),
        "environment_record": rel(environment),
        "environment_record_sha256": sha256(environment),
    }


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def parse_clock_enable() -> dict[str, Any]:
    report = RESULTS / "pure_rtl_100mhz_power_opt" / "pure_rtl_100mhz_power_opt_transformations.rpt"
    text = report.read_text(encoding="utf-8", errors="replace")
    pattern = r"\| Number of Slice Registers\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([0-9.]+)"
    match = re.search(pattern, text)
    if not match:
        raise ValueError("cannot parse slice-register clock gating summary")
    return {
        "evidence_class": "ESTIMATED",
        "vivado_operation": "power_opt_design",
        "functional_rtl_changed": False,
        "slice_registers_total": int(match.group(1)),
        "slice_registers_user_gated": int(match.group(2)),
        "slice_registers_tool_gated": int(match.group(3)),
        "slice_registers_percent_gated": float(match.group(4)),
        "raw_report": rel(report),
        "raw_report_sha256": sha256(report),
    }


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records_by_key = {(row["case_id"], row["mode"]): row for row in manifest["records"]}
    parsed: list[dict[str, Any]] = []
    for implementation_dir in sorted(path for path in ACTIVITY_POWER.iterdir() if path.is_dir()):
        implementation = implementation_dir.name
        for report in implementation_dir.rglob("*_power_post_route.rpt"):
            prefix = report.name.removesuffix("_power_post_route.rpt")
            mode = "streaming_1ksps_prefix" if "_streaming_1ksps_prefix_" in prefix else "burst_full_record"
            suffix = f"_{mode}_{implementation}"
            case_id = prefix.removesuffix(suffix)
            record = records_by_key[(case_id, mode)]
            parsed.append(
                parse_record(
                    implementation,
                    record,
                    report,
                    report.with_name(f"{prefix}_environment.txt"),
                    report.with_name(f"{prefix}_saif_unmatched.rpt"),
                    report.with_name(f"{prefix}_timing_post_route.rpt"),
                )
            )
    if not parsed:
        raise SystemExit("no activity-based power reports found")

    groups: dict[str, dict[str, Any]] = {}
    for implementation in sorted({row["implementation"] for row in parsed}):
        for mode in sorted({row["mode"] for row in parsed if row["implementation"] == implementation}):
            rows = [row for row in parsed if row["implementation"] == implementation and row["mode"] == mode]
            groups[f"{implementation}:{mode}"] = {
                "count": len(rows),
                "total_on_chip_power_w": summarize([row["total_on_chip_power_w"] for row in rows]),
                "dynamic_power_w": summarize([row["dynamic_power_w"] for row in rows]),
                "device_static_power_w": summarize([row["device_static_power_w"] for row in rows]),
                "accelerator_hierarchy_dynamic_power_w": summarize(
                    [row["accelerator_hierarchy_dynamic_power_w"] for row in rows]
                ),
                "accelerator_plus_device_static_power_w": summarize(
                    [row["accelerator_plus_device_static_power_w"] for row in rows]
                ),
            }
            if mode == "burst_full_record":
                groups[f"{implementation}:{mode}"]["accelerator_allocated_energy_per_decision_mj"] = summarize(
                    [row["energy"]["accelerator_allocated_energy_per_decision_mj"] for row in rows]
                )
                groups[f"{implementation}:{mode}"]["accelerator_dynamic_energy_per_decision_mj"] = summarize(
                    [row["energy"]["accelerator_dynamic_energy_per_decision_mj"] for row in rows]
                )

    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "physical_board_power_measured": False,
        "activity_method": "Real-ECG RTL SAIF applied to routed Vivado checkpoints",
        "limitations": [
            "Streaming SAIF records are literal 100 MHz / 1 kS/s representative prefixes, not 1,800-second simulations.",
            "These are FPGA on-chip estimates, not Nexys A7 rail measurements.",
            "Ideal full-power-gating averages exclude retention, isolation, wake and switch overheads.",
        ],
        "records": parsed,
        "groups": groups,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fields = [
        "implementation", "case_id", "class_label_report", "mode", "sample_count", "literal_sample_rate_hz",
        "saif_duration_s", "evidence_class", "total_on_chip_power_w", "dynamic_power_w", "device_static_power_w",
        "accelerator_hierarchy_dynamic_power_w", "accelerator_plus_device_static_power_w",
        "power_estimation_confidence", "design_nets_matched", "timing_wns_ns", "register_primitives",
        "register_ce_pins", "register_ce_pins_with_driven_net", "total_energy_per_decision_mj",
        "dynamic_energy_per_decision_mj", "clock_gated_no_power_gating_average_power_w",
        "dynamic_duty_cycled_average_power_w", "ideal_full_power_gating_average_power_w", "raw_power_report",
        "accelerator_allocated_energy_per_decision_mj", "accelerator_dynamic_energy_per_decision_mj",
        "accelerator_clock_gated_no_power_gating_average_power_w", "accelerator_dynamic_duty_cycled_average_power_w",
        "accelerator_ideal_full_power_gating_average_power_w",
        "raw_power_report_sha256", "saif", "saif_sha256",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in parsed:
            flat = {key: row.get(key, "") for key in fields}
            if row["energy"]:
                flat.update({key: row["energy"].get(key, "") for key in fields if key in row["energy"]})
            writer.writerow(flat)

    ce = parse_clock_enable()
    CE_JSON.write_text(json.dumps(ce, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with CE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ce), lineterminator="\n")
        writer.writeheader()
        writer.writerow(ce)
    print(OUT_JSON)
    print(OUT_CSV)
    print(CE_JSON)
    print(CE_CSV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
