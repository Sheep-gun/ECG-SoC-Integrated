# Accelerator-Benefit Benchmark

This directory is the reproducible NO_BOARD benchmark package for the locked `structural_guarded_silent_aff_1008710` SNN ECG accelerator.

- Main results: `results/accelerator_benefit_summary.csv`
- Exact Python kernel results: `results/cpu_python_kernel_summary.json`
- Exact Python end-to-end results: `results/cpu_python_end_to_end_summary.json`
- Native transaction-level Exact C++ package: `exact_cpp/`
- Native Exact C++ performance report: `exact_cpp/reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md`
- Verilator RTL-simulation host timing: `results/cpu_cpp_kernel_summary.json`
- Korean report: `reports/ACCELERATOR_BENEFIT_KR.md`
- English report: `reports/ACCELERATOR_BENEFIT_EN.md`
- Canonical RTL cycles: `results/rtl_cycle_benchmark.csv`
- Existing board audit: `reports/EXISTING_BOARD_EVIDENCE_AUDIT.md`
- Future-board checklist: `READY_FOR_BOARD_BENCHMARK.md`
- Figures: `figures/FIGURE_INDEX.md`

Regenerate and verify:

```powershell
python benchmarks/accelerator_benefit/tools/generate_benchmark_artifacts.py
python benchmarks/accelerator_benefit/tools/check_benchmark_integrity.py
```

The benchmark-scoped Python clock model matches the current cadence-sensitive RTL for all 36 cases (`final_pred` and all four `final_mem` values). Its single-process, single-thread kernel and end-to-end timings use three warmups and ten measured repetitions per case. The like-for-like stored-data comparison reports a 2288.745397x Python-kernel-to-RTL speedup.

Only the hand-written single-thread transaction-level **Exact C++** implementation is the native CPU inference baseline: 36/36 final predictions, 144/144 final membranes, and 1,080/1,080 Snapshot boundaries match; its measured 360-run kernel median is 1777.699800 ms. Comparing that measured CPU median with the cycle-derived FPGA-core latency gives an explicitly scoped 32.912687x estimate, not measured board speedup.

The separately retained Verilator artifact is a generated cycle-accurate **RTL simulation/verification runtime**. Its host timing is not labeled as Exact C++, is not treated as a CPU inference baseline, and has no CPU-baseline speedup claim. Physical board timing and power remain `PENDING_BOARD`.
