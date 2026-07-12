# Exact C++ performance benchmark

## Gate status

Timing was authorized only after the following checks passed again:

| Gate | Result |
|---|---:|
| Exact C++ final prediction | 36/36 |
| Four final membrane values | 144/144 |
| Snapshot boundaries | 1,080/1,080 |
| Representative accepted-sample state hashes | pass, four classes |
| Fixed-width primitives | 793,595 checks, zero failures |
| Module/adversarial microtraces | 18/18 |
| Debug/Release output identity | 36/36 |
| Input SHA-256 | 36/36 |

The timed classifier sources were byte-identical to clean Exact-C++ commit `fb4f77fc5faa34073697cc5cf6ad07c188e0aff1`. The build used Release, `-O3 -DNDEBUG -march=native`, and tracing disabled.

## Measured CPU results

Statistics below are over all 360 measured repetitions per mode (36 cases × 10). Standard deviation is the sample standard deviation. Each run processes 1,800,000 samples.

| Metric | Kernel-only | End-to-end |
|---|---:|---:|
| Median latency | 1777.699800 ms | 2007.549250 ms |
| Mean latency | 1782.070826 ms | 1999.155130 ms |
| Standard deviation | 79.435145 ms | 85.839932 ms |
| Minimum | 1646.875500 ms | 1847.423200 ms |
| Maximum | 2107.561200 ms | 2307.294700 ms |
| Median samples/s | 1,012,544.413 | 896,615.633 |
| Mean samples/s | 1,012,034.668 | 902,038.715 |
| Median thread cycles | 4,241,182,513.5 | 4,794,892,985.0 |
| Median cycles/sample | 2356.212508 | 2663.829436 |
| Median effective-clock estimate | 2390.209 MHz | 2390.139 MHz |
| Exact measured outputs | 360/360 | 360/360 |

Kernel case-level medians range from 1647.770500 ms (`ARR_mitdb_208_chunk00`) to 1857.826700 ms (`AFF_afdb_06995_chunk14`). End-to-end case-level medians range from 1850.635700 ms (`AFF_afdb_06995_chunk01`) to 2074.016000 ms (`CHF_chfdb_chf15_chunk03`). Exact per-case median, mean, standard deviation, minimum, maximum, throughput, cycles, and clock estimates are in `results/exact_cpp_cpu_summary.csv`.

Kernel-only excludes file access, parsing, result serialization, hash checking, validation, and CSV logging. End-to-end begins immediately before file open and ends after the result JSON is flushed. Process startup is excluded from both.

## FPGA reference verification

The committed FPGA artifact was rechecked before comparison:

| Field | Canonical value |
|---|---:|
| Accepted samples | 1,800,000 |
| `sample_gap_cycles` | 2 |
| Profile total cycles | 5,401,260 |
| Implemented clock | 100 MHz |
| Cycle-derived FPGA accelerator-core latency | 54.0126 ms |

`54.0126 ms` is **cycle-derived FPGA accelerator-core latency**. It is not measured board system latency. It excludes host transfer, MicroBlaze/UART control and transport overhead, board software, and board power/energy.

## Estimated comparison

Using the requested formula:

`1777.699800 ms / 54.0126 ms = 32.912687×`

The result is named:

**single-thread Exact C++ versus cycle-derived FPGA-core speedup estimate: 32.912687×**

Under these documented conditions, the cycle-derived FPGA core latency is approximately 32.91 times lower than the measured single-thread Exact C++ kernel latency. This is an estimate combining measured CPU latency with cycle-derived FPGA core latency; it is not a measured FPGA or board speedup.

## Verification runtimes are not CPU baselines

| Implementation | Role in this study | Native CPU inference baseline? | Performance comparison use |
|---|---|---:|---|
| Hand-written Exact C++ | Measured single-thread transaction-level inference | Yes | CPU side of the estimate |
| Python cycle-explicit model | Semantic verification and parameter parsing | No | Not used |
| Verilator-generated/event-driven model | RTL verification when available | No | Not used |

Python interpreter and Verilator simulator runtimes are intentionally excluded from the CPU-versus-FPGA comparison.

## Board status and limitations

- Board system latency: `PENDING_BOARD`.
- Host/board transfer latency: `PENDING_BOARD`.
- MicroBlaze/UART overhead: `PENDING_BOARD`.
- Board power: `PENDING_BOARD`.
- Board energy: `PENDING_BOARD`.

Temperature telemetry and explicit throttling status were unavailable because the restricted Windows session denied the thermal WMI query. Clock telemetry was stable near 2.4 GHz, but the report does not infer a stronger thermal claim. `QueryThreadCycleTime` cycles/sample is supporting evidence with a dynamic-frequency caveat; QPC latency is the primary metric.

## Evidence artifacts

- `results/exact_cpp_cpu_raw.csv`: 720 measured rows; SHA-256 `7dc3b65fe0316d08f6a6e3b740427d91340effe6f5abb598885e5f98a782bee9`.
- `results/exact_cpp_cpu_summary.csv`: case and all-case statistics; SHA-256 `784844b860ac698af4c42a4d5d995e251ae9acde86be388aade1e06997fedbc5`.
- `results/cpu_fpga_comparison.csv`: scoped comparison and `PENDING_BOARD` statuses; SHA-256 `6152e1e78e18ed7d3025d44ed2c0e27f86a0a17232ed5015e11350a5b4afa315`.
- `reports/BENCHMARK_ENVIRONMENT.md`: host, compiler, flags, affinity, power condition, timing sources, and telemetry limitations.
