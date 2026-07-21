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
DEFAULT_OUTPUT = BOARD / "future_run"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="UART port, for example COM8; required unless --dry-run")
    parser.add_argument("--baud", type=int, default=230400)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry", type=int, default=1)
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--no-program-each-case",
        action="store_true",
        help="reuse the currently programmed BIT/ELF instead of programming before each case",
    )
    args = parser.parse_args()
    if not args.dry_run and not args.port:
        parser.error("--port is required unless --dry-run is used")
    if not ELF.exists():
        raise SystemExit(f"instrumented ELF missing: {ELF}; follow board/README.md build step")
    output_dir = args.output_dir.resolve()
    command = [
        sys.executable,
        str(REPO / "tools" / "board_replay" / "run_full_record_batch_36.py"),
        "--cases", str(CASES),
        "--baud", str(args.baud),
        "--bit", str(BIT),
        "--elf", str(ELF),
        "--output-dir", str(output_dir),
        "--retry", str(args.retry),
    ]
    if args.port:
        command.extend(["--port", args.port])
    if args.resume:
        command.append("--resume")
    if args.max_cases is not None:
        command.extend(["--max-cases", str(args.max_cases)])
    if args.dry_run:
        command.append("--dry-run")
    if args.no_program_each_case:
        command.append("--no-program-each-case")
    completed = subprocess.run(command, cwd=REPO, check=False)
    if completed.returncode:
        return completed.returncode
    if args.dry_run or args.max_cases is not None:
        return 0
    return subprocess.run(
        [
            sys.executable,
            str(BOARD / "parse_board_benchmark.py"),
            "--transcripts", str(output_dir / "transcripts"),
            "--output", str(BOARD / "board_timing_results.csv"),
        ],
        cwd=REPO,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
