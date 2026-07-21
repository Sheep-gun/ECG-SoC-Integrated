#!/usr/bin/env python3
"""Parse future hardware-timer UART records into the locked result schema."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
CASES = REPO / "reports" / "final" / "board_replay_36_cases.csv"
DEFAULT_TRANSCRIPTS = REPO / "benchmarks" / "accelerator_benefit" / "board" / "future_run" / "transcripts"
DEFAULT_OUT = REPO / "benchmarks" / "accelerator_benefit" / "board" / "board_timing_results.csv"
CLASSES = ("NSR", "CHF", "ARR", "AFF")
FIELDS = [
    "case_id", "sample_count", "core_cycles", "core_latency_ms",
    "system_cycles", "system_latency_ms", "samples_per_second", "realtime_margin",
    "profile_total_cycles", "profile_run_cycles", "profile_input_wait_cycles",
    "profile_accepted_samples", "core_active_cycles", "core_active_latency_ms",
    "core_run_active_cycles", "core_run_active_latency_ms", "non_run_overhead_cycles",
    "core_active_samples_per_second", "core_active_realtime_margin",
    "final_pred", "final_mem_NSR", "final_mem_CHF", "final_mem_ARR", "final_mem_AFF",
    "pred_match", "mem_match", "timing_source", "timer_frequency_hz",
]


def read_cases() -> dict[str, dict[str, str]]:
    with CASES.open(newline="", encoding="utf-8-sig") as handle:
        return {row["case_id"]: row for row in csv.DictReader(handle)}


def parse_tokens(text: str) -> dict[str, str]:
    matches = re.findall(r"^BOARD_BENCH\s+(.+)$", text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one BOARD_BENCH line, found {len(matches)}")
    return dict(re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", matches[0]))


def parse_profile_tokens(text: str) -> dict[str, str]:
    lines = re.findall(r"^BOARD_PROFILE\s+(.+)$", text, re.MULTILINE)
    tokens: dict[str, str] = {}
    for line in lines:
        for key, value in re.findall(r"([A-Za-z0-9_]+)=([^\s]+)", line):
            if key in tokens:
                raise ValueError(f"duplicate BOARD_PROFILE token: {key}")
            tokens[key] = value
    required = {
        f"profile_{name}_{half}"
        for name in ("total", "run", "input_wait", "accepted", "windows", "decisions")
        for half in ("lo", "hi")
    }
    missing = sorted(required - set(tokens))
    if missing:
        raise ValueError(f"missing BOARD_PROFILE tokens: {', '.join(missing)}")
    return tokens


def u64(tokens: dict[str, str], base: str) -> int:
    lo = int(tokens[f"{base}_lo"], 0)
    hi = int(tokens[f"{base}_hi"], 0)
    return (hi << 32) | lo


def parse_one(path: Path, expected: dict[str, str]) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.count("SNN_ECG_FULL_REPLAY_BOARD_PASS") != 1:
        raise ValueError("expected exactly one BOARD_PASS marker")
    tokens = parse_tokens(text)
    profile = parse_profile_tokens(text)
    frequency = int(tokens["timer_frequency_hz"], 0)
    core_cycles = u64(tokens, "core_cycles")
    system_cycles = u64(tokens, "system_cycles")
    profile_total = u64(profile, "profile_total")
    profile_run = u64(profile, "profile_run")
    profile_input_wait = u64(profile, "profile_input_wait")
    profile_accepted = u64(profile, "profile_accepted")
    profile_windows = u64(profile, "profile_windows")
    profile_decisions = u64(profile, "profile_decisions")
    samples = int(tokens["sample_count"], 0)
    final_pred = int(tokens["final_pred"], 0)
    memories = {cls: int(tokens[f"final_mem_{cls}"], 0) for cls in CLASSES}
    if frequency <= 0 or core_cycles <= 0 or system_cycles <= 0:
        raise ValueError("timer frequency and core/system cycles must be positive")
    if not (profile_total == core_cycles == system_cycles):
        raise ValueError("profile-total/core/system counter equality failed")
    if not (0 <= profile_input_wait <= profile_run <= profile_total):
        raise ValueError("profile counter ordering failed")
    if profile_accepted != samples or profile_windows != 30 or profile_decisions != 1:
        raise ValueError("profile accepted/window/decision invariant failed")
    core_active_cycles = profile_total - profile_input_wait
    core_run_active_cycles = profile_run - profile_input_wait
    non_run_overhead_cycles = profile_total - profile_run
    if core_active_cycles <= 0 or core_run_active_cycles <= 0:
        raise ValueError("active-cycle result must be positive")
    core_ms = core_cycles * 1000.0 / frequency
    system_ms = system_cycles * 1000.0 / frequency
    throughput = samples / (system_ms / 1000.0)
    core_active_ms = core_active_cycles * 1000.0 / frequency
    core_run_active_ms = core_run_active_cycles * 1000.0 / frequency
    core_active_throughput = samples / (core_active_ms / 1000.0)
    return {
        "case_id": expected["case_id"],
        "sample_count": samples,
        "core_cycles": core_cycles,
        "core_latency_ms": f"{core_ms:.9f}",
        "system_cycles": system_cycles,
        "system_latency_ms": f"{system_ms:.9f}",
        "samples_per_second": f"{throughput:.6f}",
        "realtime_margin": f"{throughput / 1000.0:.6f}",
        "profile_total_cycles": profile_total,
        "profile_run_cycles": profile_run,
        "profile_input_wait_cycles": profile_input_wait,
        "profile_accepted_samples": profile_accepted,
        "core_active_cycles": core_active_cycles,
        "core_active_latency_ms": f"{core_active_ms:.9f}",
        "core_run_active_cycles": core_run_active_cycles,
        "core_run_active_latency_ms": f"{core_run_active_ms:.9f}",
        "non_run_overhead_cycles": non_run_overhead_cycles,
        "core_active_samples_per_second": f"{core_active_throughput:.6f}",
        "core_active_realtime_margin": f"{core_active_throughput / 1000.0:.6f}",
        "final_pred": final_pred,
        **{f"final_mem_{cls}": memories[cls] for cls in CLASSES},
        "pred_match": str(int(final_pred == int(expected["expected_final_pred"]))),
        "mem_match": str(int(all(memories[cls] == int(expected[f"expected_final_mem_{cls}"]) for cls in CLASSES))),
        "timing_source": tokens["timing_source"],
        "timer_frequency_hz": frequency,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcripts", type=Path, default=DEFAULT_TRANSCRIPTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    expected = read_cases()
    rows = []
    failures = []
    for case_id, case in expected.items():
        path = args.transcripts / f"{case_id}.txt"
        if not path.exists():
            failures.append(f"missing transcript: {path}")
            continue
        try:
            rows.append(parse_one(path, case))
        except Exception as exc:
            failures.append(f"{case_id}: {exc}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    if failures:
        raise SystemExit("\n".join(failures))
    if len(rows) != 36:
        raise SystemExit(f"expected 36 parsed rows, got {len(rows)}")
    if not all(int(row["sample_count"]) == 1_800_000 for row in rows):
        raise SystemExit("sample-count acceptance failed")
    if not all(row["pred_match"] == "1" and row["mem_match"] == "1" for row in rows):
        raise SystemExit("functional-equivalence acceptance failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
