# Exact C/C++ Baseline

Status: **MEASURED_NOW**.

This is a Verilator-generated, cycle-accurate C++ translation of the unchanged locked RTL. It is not a hand-optimized algorithmic implementation and is not used as a substitute for the required Python reference path.

- Functional gate: 36/36 `final_pred` and 36/36 all four `final_mem` values.
- Timing: 3 untimed warmups followed by 10 measured runs per case (360 measured runs).
- Scope: samples already loaded in memory through final result, one model instance, one host thread.
- Per-case-median aggregate latency: median 2456.708125 ms, mean 2526.432594 ms, population standard deviation 216.383249 ms, IQR 14.722087 ms.
- Median measured throughput: 0.732031 MSamples/s.

This host timing is reported independently. It is not combined with the RTL's cycle-derived stored-data latency to claim a Python speedup.
