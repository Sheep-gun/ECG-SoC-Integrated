# Exact Python Baseline

Status: **MEASURED_NOW**. The benchmark-scoped Python clock model holds the delayed accepted sample exactly as the locked RTL pipeline does and uses canonical `sample_gap_cycles=2`.

- Functional gate: 36/36 `final_pred` and 36/36 all four `final_mem` values.
- Timing: one process, forced one-thread numerical environment, 3 warmups and 10 measured repetitions per case using `time.perf_counter_ns()`.
- Kernel per-case-median aggregate: median 123621.089625 ms, mean 124842.579046 ms, population standard deviation 5978.646000 ms, min 118065.864350 ms, max 143083.777550 ms, IQR 3260.197975 ms.
- End-to-end per-case-median aggregate: median 123726.935600 ms, mean 124954.767919 ms, population standard deviation 5985.673527 ms, min 118168.048800 ms, max 143209.749300 ms, IQR 3269.946075 ms.
