# Exact C++ benchmark environment

## Identity

- Measurement date: 2026-07-12, Asia/Seoul.
- Exact C++ branch/commit: `codex/exact-cpp-baseline` / `fb4f77fc5faa34073697cc5cf6ad07c188e0aff1`.
- Locked digital commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`.
- Model: `structural_guarded_silent_aff_1008710`.
- Parameter payload SHA-256: `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b`.
- Measured executable SHA-256: `a22ef69ee7af3d6d64714cd5925755e134fe35db79a6d18db5722c75c07a2e49`.
- Benchmark harness source SHA-256: `569a82216fd7cb9b2fb677182831588aea4549eddfbb7fe4b75a7bba9c97120a`.
- Raw measurement SHA-256: `7dc3b65fe0316d08f6a6e3b740427d91340effe6f5abb598885e5f98a782bee9`.

The classifier `include/` and `src/` files used to build the harness were byte-compared with the clean Exact-C++ worktree before timing. All 36 input SHA-256 values were also rechecked against the committed manifest.

## Host

- CPU: `AMD Ryzen 9 7940HX with Radeon Graphics`.
- CPUID: `AMD64 Family 25 Model 97 Stepping 2`, `AuthenticAMD`.
- Topology: 16 physical cores, 32 logical processors. CPUID reports 32 logical execution units and 2 threads per core. The preliminary runtime JSON's `physical_cores: 32` is an initial decoder limitation and is superseded by this CPUID topology result.
- OS registry identity: Windows 10 Home, display version 25H2, build `26200.8655`, x86-64 client. Windows product naming in this registry value may be legacy; the build number is retained verbatim.
- Memory capacity could not be queried through CIM in the restricted measurement session and was not inferred.

## Toolchain and build

- Compiler: GNU C++ 6.2.0, MSYS2/Xilinx distribution.
- CMake: 3.25.0.
- Ninja: 1.13.1.
- Language: C++17 (`-std=c++1z` in this compiler).
- Effective compile flags: `-O3 -DNDEBUG -Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -march=native`.
- `EXACT_CPP_TRACE=0`; no Snapshot trace collection or trace I/O.
- Assertions disabled by `NDEBUG`.
- No hand-written SIMD, OpenMP, worker threads, or parallel case execution.
- One benchmark process; the process had one observed thread.

## CPU scheduling and power condition

- Processor group: 0.
- Fixed affinity: logical CPU 2, mask `0x4`, for both process and benchmark thread.
- Process/thread priority: normal default; no real-time priority was requested.
- Active Windows power plan: Balanced (`381b4222-f694-41f0-9685-ff5bb260df2e`).
- AC minimum processor state: 80%.
- AC maximum processor state: 100%.
- No artificial 100 MHz cap or FPGA-frequency matching was applied.
- Hidden boost-mode policy could not be read in the restricted session. The benchmark did not change boost settings.
- Processor power information reported 2401 MHz current/max/limit throughout sampled rows.
- Median cycle-derived effective clock estimate: 2390.209 MHz for kernel-only and 2390.139 MHz end-to-end.

Temperature access through `MSAcpi_ThermalZoneTemperature` was denied. Consequently temperature and an explicit hardware throttling flag are unavailable. The reported/effective clocks were stable near 2.4 GHz, but this is not sufficient to prove that thermal or firmware throttling never occurred; the benchmark makes no stronger claim.

## Timing and cycle counters

- Wall-clock source: Windows `QueryPerformanceCounter`, frequency 10,000,000 Hz.
- CPU cycles: Windows `QueryThreadCycleTime`, available for all 720 measured rows.
- Cycle counts are per-thread and affinity was fixed. Dynamic-frequency/power-management behavior means cycles/sample is supporting evidence rather than the primary comparison metric.
- Primary comparison metric: QPC kernel-only latency.

## Protocol

- 36 locked cases, 1,800,000 signed 12-bit samples each.
- Kernel-only input was parsed and preloaded into RAM before any timed kernel region.
- Three warmups followed by ten measured repetitions for every case and each mode.
- Kernel-only timed region: preloaded samples to final prediction/four final membranes.
- End-to-end timed region: file open, signed-12 hex parsing, inference, JSON output write/flush.
- Process launch, input hash verification, warmups, output comparison, power sampling, and CSV recording were outside the timed regions.
- Every warmup and measured result was checked against the locked expected output.

An initial run was terminated by the orchestration tool's 20-minute command timeout after producing an incomplete partial CSV. That file was discarded. The accepted dataset comes from a fresh, complete single-process run with a one-hour command limit. The preceding attempt may have left the CPU in a sustained warm condition; the complete run still performed the specified per-case warmups.
