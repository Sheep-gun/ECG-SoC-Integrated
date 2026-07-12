# Accelerator-Benefit Benchmark

This directory is the reproducible NO_BOARD benchmark package for the locked `structural_guarded_silent_aff_1008710` SNN ECG accelerator.

- Main results: `results/accelerator_benefit_summary.csv`
- Exact Python kernel results: `results/cpu_python_kernel_summary.json`
- Exact Python end-to-end results: `results/cpu_python_end_to_end_summary.json`
- Exact C++ RTL-translation results: `results/cpu_cpp_kernel_summary.json`
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

The benchmark-scoped Python clock model matches the current cadence-sensitive RTL for all 36 cases (`final_pred` and all four `final_mem` values). Its single-process, single-thread kernel and end-to-end timings use three warmups and ten measured repetitions per case. The like-for-like stored-data comparison reports a 2288.745397x Python-kernel-to-RTL speedup. The exact Verilator-generated C++ RTL translation is measured separately after the same 36/36 output-equivalence gate; it is not a hand-optimized algorithm or a substitute for the Python reference path. Physical board timing and power remain `PENDING_BOARD`.
