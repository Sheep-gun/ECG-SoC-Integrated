# Accelerator-Benefit Benchmark

This directory is the reproducible NO_BOARD benchmark package for the locked `structural_guarded_silent_aff_1008710` SNN ECG accelerator.

- Main results: `results/accelerator_benefit_summary.csv`
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

CPU and C/C++ timings are intentionally absent because the repository's removed historical Python model failed equivalence to the final cadence-sensitive RTL. No CPU speedup is claimed.
