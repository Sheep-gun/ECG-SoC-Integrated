#!/usr/bin/env python3
"""Deterministic future-board launcher; never probes hardware in NO_BOARD mode."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
BOARD = REPO / "benchmarks" / "accelerator_benefit" / "board"
CASES = REPO / "reports" / "final" / "board_replay_36_cases.csv"
BIT = REPO / "results" / "board_replay" / "microblaze_full_replay" / "snn_ecg_mb_full_replay.bit"
ELF = BOARD / "build" / "snn_ecg_mb_full_replay_benchmark.elf"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="UART port, for example COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--program", action="store_true")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if not ELF.exists():
        raise SystemExit(f"instrumented ELF missing: {ELF}; follow board/README.md build step")
    command = [
        sys.executable,
        str(REPO / "tools" / "board_replay" / "run_full_record_batch_36.py"),
        "--cases", str(CASES),
        "--port", args.port,
        "--baud", str(args.baud),
        "--bit", str(BIT),
        "--elf", str(ELF),
        "--output-dir", str(BOARD / "future_run"),
    ]
    if args.program:
        command.append("--program")
    if args.resume:
        command.append("--resume")
    completed = subprocess.run(command, cwd=REPO, check=False)
    if completed.returncode:
        return completed.returncode
    return subprocess.run(
        [
            sys.executable,
            str(BOARD / "parse_board_benchmark.py"),
            "--transcripts", str(BOARD / "future_run" / "transcripts"),
            "--output", str(BOARD / "board_timing_results.csv"),
        ],
        cwd=REPO,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
