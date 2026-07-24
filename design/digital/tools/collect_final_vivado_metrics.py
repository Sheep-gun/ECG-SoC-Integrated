#!/usr/bin/env python3
"""Validate final Vivado metrics against the committed MicroBlaze build summary."""

from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FINAL_METRICS = REPO / "reports" / "final" / "final_metrics.json"
MB_SUMMARY = REPO / "results" / "board_replay" / "microblaze_full_replay" / "microblaze_full_replay_summary.json"


def as_int(value: object) -> int:
    return int(str(value))


def as_bool(value: object, name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise TypeError(f"{name} must be a JSON boolean, got {value!r}")


def main() -> int:
    final = json.loads(FINAL_METRICS.read_text(encoding="utf-8"))
    mb = json.loads(MB_SUMMARY.read_text(encoding="utf-8"))
    util = mb["utilization"]
    timing = mb["timing"]

    observed = {
        "microblaze_full_replay_system": {
            "lut": as_int(util["slice_lut"]),
            "slice_reg": as_int(util["slice_reg"]),
            "bram": as_int(util["bram_tile"]),
            "dsp": as_int(util["dsp"]),
            "setup_wns_ns": float(timing["setup_worst_slack_ns"]),
            "hold_wns_ns": float(timing["hold_worst_slack_ns"]),
            "timing_constraints_met": as_bool(mb["timing_constraints_met"], "timing_constraints_met"),
        },
        "bitstream_exists": as_bool(mb["bitstream_exists"], "bitstream_exists"),
        "xsa_exists": as_bool(mb["xsa_exists"], "xsa_exists"),
    }

    failures: list[str] = []
    expected = final["microblaze_full_replay_system"]
    for key, value in observed["microblaze_full_replay_system"].items():
        if expected.get(key) != value:
            failures.append(f"microblaze_full_replay_system.{key}: expected {value}, got {expected.get(key)}")
    if not observed["bitstream_exists"]:
        failures.append("bitstream is missing")
    if not observed["xsa_exists"]:
        failures.append("XSA is missing")

    print(json.dumps(observed, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit("\n".join(failures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
