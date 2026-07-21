# Board Timing Package

Status: **COMPLETED** on Nexys A7-100T, `COM8`, 230400 baud.

The immutable BIT and instrumented ELF were programmed before each case. All 36 cases sent 1,800,000 samples, produced 30 snapshots and one decision, emitted exactly one `BOARD_BENCH` line and a board PASS marker, and matched Golden Reference final predictions 36/36 and all Final Membrane values 144/144.

The reportable accelerator performance metric is `core_active_cycles = profile_total_cycles - profile_input_wait_cycles`. Both operands are measured 100 MHz hardware counters. The RTL increments `profile_input_wait` only in RUN while the accelerator is ready and `sample_valid` is absent, so the subtraction removes upstream UART/MicroBlaze starvation but retains internal back-pressure, snapshot/final-decision work, and 1,320 non-RUN control cycles. All 36 cases produced exactly 3601290 active cycles (36.012900 ms), matching the canonical XSim subtraction 36/36.

Raw `core_cycles` and `system_cycles` are retained unchanged as UART-paced transaction diagnostics; they were equal in 36/36 cases. They are not used for accelerator speedup or energy. Integrated-system compute latency, speedup, and energy remain unmeasured because the immutable XSA has no preloaded input path or independent AXI Timer. UART result printing occurs after counters stop. The integrated AXI UARTLite is configured for 230400 baud; 115200 produces undecodable bytes.

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
