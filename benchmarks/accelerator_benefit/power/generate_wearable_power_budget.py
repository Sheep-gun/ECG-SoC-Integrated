#!/usr/bin/env python3
"""Generate an evidence-labeled wearable system power budget."""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "benchmarks" / "accelerator_benefit" / "power" / "results"
ACTIVITY = RESULTS / "activity_power_summary.json"
OUT_CSV = RESULTS / "wearable_power_budget.csv"
OUT_JSON = RESULTS / "wearable_power_budget.json"


def main() -> int:
    payload = json.loads(ACTIVITY.read_text(encoding="utf-8"))
    baseline = [row for row in payload["records"] if row["implementation"] == "baseline"]
    streaming = [row for row in baseline if row["mode"] == "streaming_1ksps_prefix"]
    burst = [row for row in baseline if row["mode"] == "burst_full_record"]
    if not streaming or not burst:
        raise SystemExit("baseline streaming and burst activity reports are required")
    stream_total = statistics.median(row["accelerator_plus_device_static_power_w"] for row in streaming)
    stream_dynamic = statistics.median(row["accelerator_hierarchy_dynamic_power_w"] for row in streaming)
    burst_no_pg = statistics.median(
        row["energy"]["accelerator_clock_gated_no_power_gating_average_power_w"] for row in burst
    )
    burst_dynamic = statistics.median(row["energy"]["accelerator_dynamic_duty_cycled_average_power_w"] for row in burst)
    burst_ideal_pg = statistics.median(row["energy"]["accelerator_ideal_full_power_gating_average_power_w"] for row in burst)

    rows = [
        {
            "scenario": "fpga_streaming_always_clocked", "component": "ECG AFE/ADC", "evidence_class": "EXTERNAL_DATASHEET",
            "power_w": 0.000085, "status": "REFERENCE_ONLY",
            "basis": "MAX30001 ECG channel typical power; verify exact configuration",
        },
        {
            "scenario": "fpga_streaming_always_clocked", "component": "Pure RTL FPGA on-chip", "evidence_class": "ESTIMATED",
            "power_w": stream_total, "status": "AVAILABLE",
            "basis": "Median post-route literal-1-kS/s ECG SAIF Total On-Chip Power",
        },
        {
            "scenario": "fpga_streaming_always_clocked", "component": "Pure RTL FPGA dynamic subset", "evidence_class": "ESTIMATED",
            "power_w": stream_dynamic, "status": "AVAILABLE",
            "basis": "Median post-route literal-1-kS/s ECG SAIF Dynamic Power; subset, not additive",
        },
        {
            "scenario": "fpga_preloaded_burst_30min", "component": "Pure RTL FPGA without power gating", "evidence_class": "DERIVED",
            "power_w": burst_no_pg, "status": "AVAILABLE",
            "basis": "FPGA static plus active dynamic scaled by 36.0129 ms / 1800 s; assumes global clock gating while idle",
        },
        {
            "scenario": "fpga_preloaded_burst_30min", "component": "Pure RTL dynamic subset", "evidence_class": "DERIVED",
            "power_w": burst_dynamic, "status": "AVAILABLE",
            "basis": "Active FPGA dynamic scaled by 36.0129 ms / 1800 s; subset, not additive",
        },
        {
            "scenario": "idealized_power_gated_ip", "component": "Pure RTL FPGA-equivalent IP", "evidence_class": "DERIVED",
            "power_w": burst_ideal_pg, "status": "UPPER_BOUND_ASSUMPTION",
            "basis": "Active total energy / 1800 s; excludes retention, isolation, wake, switch and off leakage",
        },
    ]
    for scenario in ("fpga_streaming_always_clocked", "fpga_preloaded_burst_30min", "asic_wearable_target"):
        for component in ("sample memory", "MCU/control", "BLE radio", "PMIC/regulator loss"):
            rows.append(
                {
                    "scenario": scenario,
                    "component": component,
                    "evidence_class": "MEASUREMENT_REQUIRED",
                    "power_w": "",
                    "status": "BLOCKED_COMPONENT_AND_DUTY_CYCLE_UNSPECIFIED",
                    "basis": "Select the device and workload, then measure or use the matching vendor operating point",
                }
            )
    rows.append(
        {
            "scenario": "asic_wearable_target", "component": "SNN accelerator IP", "evidence_class": "ESTIMATION_REQUIRED",
            "power_w": "", "status": "BLOCKED_NO_PDK_POST_LAYOUT",
            "basis": "Requires target-node post-layout leakage/dynamic power with real-ECG SAIF and low-power intent",
        }
    )

    fields = ["scenario", "component", "evidence_class", "power_w", "status", "basis"]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    output = {
        "schema_version": 1,
        "complete_wearable_budget_available": False,
        "reason": "Memory, MCU, BLE, PMIC workload and target ASIC post-layout power are not specified.",
        "afe_reference_url": "https://www.analog.com/en/products/max30001.html",
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT_CSV)
    print(OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
