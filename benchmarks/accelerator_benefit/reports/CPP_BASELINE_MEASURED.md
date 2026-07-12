# Verilator RTL Simulation Host Timing

Status: **MEASURED_NOW**.

This is host timing of a Verilator-generated, cycle-accurate simulation model of the unchanged locked RTL. It is **not** the hand-written Exact C++ native CPU inference baseline and is not treated as an optimized CPU implementation.

- Functional gate: 36/36 `final_pred` and 36/36 all four `final_mem` values.
- Timing: 3 untimed warmups followed by 10 measured runs per case (360 measured runs).
- Scope: samples already loaded in memory through final result, one model instance, one host thread.
- Per-case-median aggregate latency: median 2456.708125 ms, mean 2526.432594 ms, population standard deviation 216.383249 ms, IQR 14.722087 ms.
- Median measured throughput: 0.732031 MSamples/s.

This simulation-runtime timing is reported independently and has no CPU-baseline speedup claim. The native CPU baseline is documented under `exact_cpp/`.
