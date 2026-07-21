# Board Timing Package

Status: **COMPLETED** on Nexys A7-100T, `COM8`, 230400 baud.

The immutable BIT and instrumented ELF were programmed before each case. All 36 cases sent 1,800,000 samples, produced 30 snapshots and one decision, emitted exactly one `BOARD_BENCH` line and a board PASS marker, and matched Golden Reference final predictions 36/36 and all Final Membrane values 144/144.

`core_cycles` is the accelerator last-decision hardware counter. `system_cycles` is the accelerator total transaction counter. UART result printing occurs after both counters stop. The immutable XSA has no independent AXI Timer, so neither value is relabeled as host wall latency. Core and system counters were equal in 36/36 cases because both counters stop at the final decision and the measured interval includes UART-paced input wait. `profile_input_wait` is retained only as a DERIVED diagnostic in `board_timing_summary.json`; it is not substituted for the required measured core/system counters. The integrated AXI UARTLite in the immutable BIT is configured for 230400 baud; 115200 produces undecodable bytes.

Reproduce the manifest-only preflight:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --dry-run --output-dir benchmarks/accelerator_benefit/board/preflight_dry_run
```

Re-run or resume the board batch:

```powershell
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port COM8
python benchmarks/accelerator_benefit/board/run_board_benchmark.py --port COM8 --resume
```

The 36-case runner programs each case by default. It does not accept or require `--program`. Raw transcripts are under `board/future_run/transcripts`; parsed JSON, batch summaries, and `board_timing_results.csv` are retained beside them.
