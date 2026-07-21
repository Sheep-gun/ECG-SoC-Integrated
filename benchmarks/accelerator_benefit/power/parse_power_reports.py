#!/usr/bin/env python3
"""Parse raw Vivado post-route reports into the benchmark power source of truth."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[3]
POWER = REPO / "benchmarks" / "accelerator_benefit" / "power"
RESULTS = POWER / "results"
SUMMARY_JSON = RESULTS / "power_summary.json"
SUMMARY_CSV = RESULTS / "power_summary.csv"

SCOPES = {
    "pure_rtl_1mhz": {
        "label": "Pure RTL accelerator, 1 MHz core",
        "directory": RESULTS / "pure_rtl",
        "power": "pure_rtl_power_post_route.rpt",
        "utilization": "pure_rtl_utilization_post_route.rpt",
        "timing": "pure_rtl_timing_post_route.rpt",
        "environment": "pure_rtl_environment.txt",
        "checkpoint": POWER / "work" / "pure_rtl" / "pure_rtl_routed.dcp",
        "core_clock_frequency_mhz": 1.0,
        "clock_configuration": "100 MHz board input divided by 100 to a 1 MHz generated accelerator core clock",
    },
    "pure_rtl_100mhz": {
        "label": "Pure RTL accelerator, direct 100 MHz core",
        "directory": RESULTS / "pure_rtl_100mhz",
        "power": "pure_rtl_100mhz_power_post_route.rpt",
        "utilization": "pure_rtl_100mhz_utilization_post_route.rpt",
        "timing": "pure_rtl_100mhz_timing_post_route.rpt",
        "environment": "pure_rtl_100mhz_environment.txt",
        "checkpoint": POWER / "work" / "pure_rtl_100mhz" / "pure_rtl_100mhz_routed.dcp",
        "build_manifest": "pure_rtl_100mhz_build_manifest.json",
        "core_clock_frequency_mhz": 100.0,
        "clock_configuration": "Direct 100 MHz board clock; no generated or divided accelerator core clock",
    },
    "microblaze_system": {
        "label": "MicroBlaze full-replay integrated FPGA system",
        "directory": RESULTS / "microblaze_system",
        "power": "system_power_post_route.rpt",
        "utilization": "system_utilization_post_route.rpt",
        "timing": "system_timing_post_route.rpt",
        "environment": "system_environment.txt",
        "checkpoint": POWER / "work" / "microblaze_system" / "microblaze_system_routed.dcp",
        "core_clock_frequency_mhz": 100.0,
        "clock_configuration": "MicroBlaze full-replay system and accelerator use the constrained 100 MHz system clock",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def portable_path(value: str | None) -> str | None:
    if not value:
        return value
    try:
        return rel(Path(value))
    except (OSError, ValueError):
        return value


def required(pattern: str, text: str, field: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"cannot parse {field}")
    return match.group(1).strip()


def optional(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else None


def read_environment(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {"clocks": []}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("CLOCK="):
            match = re.fullmatch(r"CLOCK=(\S+) PERIOD_NS=([0-9.]+)", line)
            if match:
                period = float(match.group(2))
                values["clocks"].append(
                    {
                        "name": match.group(1),
                        "period_ns": period,
                        "frequency_mhz": 1000.0 / period,
                    }
                )
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.lower()] = value
    return values


def parse_utilization(text: str) -> dict[str, float | int | None]:
    def number(pattern: str) -> float | int | None:
        value = optional(pattern, text)
        if value is None:
            return None
        parsed = float(value)
        return int(parsed) if parsed.is_integer() else parsed

    return {
        "lut": number(r"\|\s*Slice LUTs\s*\|\s*([0-9.]+)"),
        "flip_flop": number(r"\|\s*(?:Slice Registers|Register as Flip Flop)\s*\|\s*([0-9.]+)"),
        "bram_tile": number(r"\|\s*Block RAM Tile\s*\|\s*([0-9.]+)"),
        "dsp": number(r"\|\s*DSPs\s*\|\s*([0-9.]+)"),
    }


def parse_timing(text: str) -> dict[str, float | None]:
    wns = optional(r"WNS\(ns\).*?\n[-+|\s]*\n\s*\|?\s*([-0-9.]+)", text)
    if wns is None:
        wns = optional(r"Slack \(MET\)\s*:\s*([-0-9.]+)ns", text)
    return {"wns_ns": float(wns) if wns is not None else None}


def parse_scope(scope: str, config: dict[str, Any]) -> dict[str, Any]:
    directory = Path(config["directory"])
    power_path = directory / config["power"]
    util_path = directory / config["utilization"]
    timing_path = directory / config["timing"]
    env_path = directory / config["environment"]
    for path in (power_path, util_path, timing_path, env_path):
        if not path.exists():
            raise FileNotFoundError(path)

    power_text = power_path.read_text(encoding="utf-8", errors="replace")
    util_text = util_path.read_text(encoding="utf-8", errors="replace")
    timing_text = timing_path.read_text(encoding="utf-8", errors="replace")
    environment = read_environment(env_path)
    checkpoint = Path(config["checkpoint"])
    build_manifest = directory / config["build_manifest"] if config.get("build_manifest") else None

    simulation_activity = required(r"\| Simulation Activity File\s*\|\s*([^|]+)", power_text, "simulation activity file")
    confidence = optional(r"\| Overall confidence level\s*\|\s*([^|]+)", power_text)
    if confidence is None:
        confidence = required(r"\| Confidence Level\s*\|\s*([^|]+)", power_text, "confidence")

    timing = parse_timing(timing_text)
    if environment.get("timing_status"):
        timing["status"] = environment["timing_status"]
    elif timing["wns_ns"] is not None:
        timing["status"] = "MET" if timing["wns_ns"] >= 0 else "FAILED"
    else:
        timing["status"] = "UNKNOWN"

    return {
        "scope": scope,
        "label": config["label"],
        "evidence_class": "ESTIMATED",
        "estimate_description": "Post-implementation vectorless Vivado power estimate",
        "vivado_version": required(r"\| Tool Version\s*:\s*(.+)", power_text, "Vivado version"),
        "fpga_part": required(r"\| Device\s*:\s*(.+)", power_text, "FPGA part"),
        "design_top": required(r"\| Design\s*:\s*(.+)", power_text, "design top"),
        "implementation_status": required(r"\| Design State\s*:\s*(.+)", power_text, "design state"),
        "clocks": environment["clocks"],
        "core_clock_frequency_mhz": config["core_clock_frequency_mhz"],
        "clock_configuration": config["clock_configuration"],
        "total_on_chip_power_w": float(required(r"\| Total On-Chip Power \(W\)\s*\|\s*([0-9.]+)", power_text, "total power")),
        "dynamic_power_w": float(required(r"\| Dynamic \(W\)\s*\|\s*([0-9.]+)", power_text, "dynamic power")),
        "device_static_power_w": float(required(r"\| Device Static \(W\)\s*\|\s*([0-9.]+)", power_text, "static power")),
        "power_unit": "W",
        "power_estimation_confidence": confidence,
        "junction_temperature_c": float(required(r"\| Junction Temperature \(C\)\s*\|\s*([0-9.]+)", power_text, "junction temperature")),
        "activity_source": environment.get("activity_source"),
        "simulation_activity_file": simulation_activity,
        "signal_toggle_rate_assumption": environment.get("switching_activity"),
        "clock_activity": "User-constrained clocks; frequencies listed in clocks; no SAIF/VCD",
        "constraint": portable_path(environment.get("constraint")),
        "utilization": parse_utilization(util_text),
        "timing": timing,
        "raw_power_report": rel(power_path),
        "raw_power_report_sha256": sha256(power_path),
        "utilization_report": rel(util_path),
        "utilization_report_sha256": sha256(util_path),
        "timing_report": rel(timing_path),
        "timing_report_sha256": sha256(timing_path),
        "environment_record": rel(env_path),
        "environment_record_sha256": sha256(env_path),
        "build_manifest": rel(build_manifest) if build_manifest and build_manifest.exists() else None,
        "build_manifest_sha256": sha256(build_manifest) if build_manifest and build_manifest.exists() else None,
        "routed_checkpoint": rel(checkpoint) if checkpoint.exists() else None,
        "routed_checkpoint_sha256": sha256(checkpoint) if checkpoint.exists() else None,
    }


def main() -> int:
    scopes = {name: parse_scope(name, config) for name, config in SCOPES.items()}
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "ESTIMATED",
        "physical_board_power_measured": False,
        "activity_method": "Post-implementation vectorless Vivado power estimate",
        "scopes": scopes,
    }
    activity_summary = RESULTS / "activity_power_summary.json"
    clock_enable_summary = RESULTS / "clock_enable_summary.json"
    wearable_budget = RESULTS / "wearable_power_budget.json"
    if activity_summary.exists():
        payload["activity_based_power"] = {
            "path": rel(activity_summary),
            "sha256": sha256(activity_summary),
            "description": "Real-ECG SAIF post-route mode-separated power estimates",
        }
    if clock_enable_summary.exists():
        payload["clock_enable_evidence"] = {
            "path": rel(clock_enable_summary),
            "sha256": sha256(clock_enable_summary),
        }
    if wearable_budget.exists():
        payload["wearable_power_budget"] = {
            "path": rel(wearable_budget),
            "sha256": sha256(wearable_budget),
            "complete": False,
        }
    SUMMARY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fields = [
        "scope", "label", "evidence_class", "estimate_description", "vivado_version",
        "fpga_part", "design_top", "implementation_status", "core_clock_frequency_mhz", "clock_configuration", "clock_frequency_mhz",
        "total_on_chip_power_w", "dynamic_power_w", "device_static_power_w", "power_unit",
        "power_estimation_confidence", "junction_temperature_c", "activity_source",
        "simulation_activity_file", "signal_toggle_rate_assumption", "clock_activity", "constraint",
        "raw_power_report", "raw_power_report_sha256", "build_manifest", "build_manifest_sha256", "routed_checkpoint_sha256",
    ]
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in scopes.values():
            row = {key: item.get(key, "") for key in fields}
            row["clock_frequency_mhz"] = ";".join(f"{clock['name']}={clock['frequency_mhz']:.6f}" for clock in item["clocks"])
            writer.writerow(row)
    print(SUMMARY_JSON)
    print(SUMMARY_CSV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
