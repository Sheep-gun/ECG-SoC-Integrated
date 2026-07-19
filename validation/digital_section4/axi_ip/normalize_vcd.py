#!/usr/bin/env python3
"""Extract a compact, deterministic selected-signal trace from an XSim VCD."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROFILES = {
    "accelerator": {
        "reset_n": "tb_snn_ecg_axi_smoke.aresetn",
        "awvalid": "tb_snn_ecg_axi_smoke.awvalid",
        "awready": "tb_snn_ecg_axi_smoke.awready",
        "wvalid": "tb_snn_ecg_axi_smoke.wvalid",
        "wready": "tb_snn_ecg_axi_smoke.wready",
        "bvalid": "tb_snn_ecg_axi_smoke.bvalid",
        "arvalid": "tb_snn_ecg_axi_smoke.arvalid",
        "arready": "tb_snn_ecg_axi_smoke.arready",
        "rvalid": "tb_snn_ecg_axi_smoke.rvalid",
        "rready": "tb_snn_ecg_axi_smoke.rready",
        "tvalid": "tb_snn_ecg_axi_smoke.tvalid",
        "tready": "tb_snn_ecg_axi_smoke.tready",
        "tlast": "tb_snn_ecg_axi_smoke.tlast",
        "irq": "tb_snn_ecg_axi_smoke.irq",
        "start": "tb_snn_ecg_axi_smoke.dut.core_start_pulse",
        "run_active": "tb_snn_ecg_axi_smoke.dut.run_active",
        "done": "tb_snn_ecg_axi_smoke.dut.done_sticky",
        "result_valid": "tb_snn_ecg_axi_smoke.dut.result_valid_reg",
        "snapshot_index": "tb_snn_ecg_axi_smoke.dut.core_snapshot_index",
        "accepted": "tb_snn_ecg_axi_smoke.dut.samples_accepted_count",
    },
    "feeder": {
        "reset_n": "tb_axi_lite_axis_sample_feeder.rstn",
        "awvalid": "tb_axi_lite_axis_sample_feeder.awvalid",
        "awready": "tb_axi_lite_axis_sample_feeder.awready",
        "wvalid": "tb_axi_lite_axis_sample_feeder.wvalid",
        "wready": "tb_axi_lite_axis_sample_feeder.wready",
        "bvalid": "tb_axi_lite_axis_sample_feeder.bvalid",
        "arvalid": "tb_axi_lite_axis_sample_feeder.arvalid",
        "arready": "tb_axi_lite_axis_sample_feeder.arready",
        "rvalid": "tb_axi_lite_axis_sample_feeder.rvalid",
        "rready": "tb_axi_lite_axis_sample_feeder.rready",
        "tvalid": "tb_axi_lite_axis_sample_feeder.tvalid",
        "tready": "tb_axi_lite_axis_sample_feeder.tready",
        "tlast": "tb_axi_lite_axis_sample_feeder.tlast",
        "fifo_count": "tb_axi_lite_axis_sample_feeder.dut.fifo_count",
        "write_count": "tb_axi_lite_axis_sample_feeder.dut.write_count",
        "tx_count": "tb_axi_lite_axis_sample_feeder.dut.tx_count",
        "tlast_count": "tb_axi_lite_axis_sample_feeder.dut.tlast_count",
    },
}


def parse_header(lines: list[str]) -> tuple[dict[str, tuple[str, int]], int, str]:
    scope: list[str] = []
    variables: dict[str, tuple[str, int]] = {}
    timescale = "unknown"
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "$timescale":
            i += 1
            timescale = lines[i].strip()
        elif stripped.startswith("$scope "):
            parts = stripped.split()
            scope.append(parts[2])
        elif stripped == "$upscope $end":
            scope.pop()
        elif stripped.startswith("$var "):
            parts = stripped.split()
            width = int(parts[2])
            identifier = parts[3]
            name = parts[4]
            variables[".".join(scope + [name])] = (identifier, width)
        elif stripped == "$enddefinitions $end":
            return variables, i + 1, timescale
        i += 1
    raise ValueError("VCD header is missing $enddefinitions")


def parse_value(line: str) -> tuple[str, str] | None:
    if not line:
        return None
    if line[0] in "01xXzZ":
        return line[1:].strip(), line[0].lower()
    if line[0] in "bBrR":
        parts = line[1:].split()
        if len(parts) == 2:
            raw, identifier = parts
            raw = raw.lower()
            if all(ch in "01" for ch in raw):
                return identifier, str(int(raw, 2))
            return identifier, raw
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lines = args.input.read_text(encoding="utf-8", errors="replace").splitlines()
    variables, body_start, timescale = parse_header(lines)
    requested = PROFILES[args.profile]
    missing = [path for path in requested.values() if path not in variables]
    if missing:
        raise SystemExit("missing VCD signals: " + ", ".join(missing))

    identifier_to_labels: dict[str, list[str]] = {}
    signal_info: dict[str, dict[str, object]] = {}
    for label, path in requested.items():
        identifier, width = variables[path]
        identifier_to_labels.setdefault(identifier, []).append(label)
        signal_info[label] = {"path": path, "width": width, "transitions": []}

    time_ps = 0
    for raw in lines[body_start:]:
        line = raw.strip()
        if line.startswith("#"):
            time_ps = int(line[1:])
            continue
        parsed = parse_value(line)
        if parsed is None:
            continue
        identifier, value = parsed
        for label in identifier_to_labels.get(identifier, []):
            transitions = signal_info[label]["transitions"]
            if not transitions or transitions[-1][1] != value:
                transitions.append([time_ps, value])

    output = {
        "profile": args.profile,
        "source_vcd": args.input.name,
        "timescale": timescale,
        "end_time_ps": time_ps,
        "signals": signal_info,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
