# Accelerator-Benefit Benchmark

This directory is the reproducible board-performance and Vivado-power package for the locked `structural_guarded_silent_aff_1008710` SNN ECG accelerator.

- Main results: `results/accelerator_benefit_summary.csv`
- Exact Python kernel results: `results/cpu_python_kernel_summary.json`
- Exact Python end-to-end results: `results/cpu_python_end_to_end_summary.json`
- Native transaction-level Exact C++ package: `exact_cpp/`
- Native Exact C++ performance report: `exact_cpp/reports/EXACT_CPP_PERFORMANCE_BENCHMARK.md`
- Verilator RTL-simulation host timing: `results/cpu_cpp_kernel_summary.json`
- Korean report: `reports/ACCELERATOR_BENEFIT_KR.md`
- English report: `reports/ACCELERATOR_BENEFIT_EN.md`
- Canonical RTL cycles: `results/rtl_cycle_benchmark.csv`
- Completed board package: `board/`
- Board completion record: `READY_FOR_BOARD_BENCHMARK.md`
- Figures: `figures/FIGURE_INDEX.md`

Regenerate and verify:

```powershell
vivado -mode batch -source benchmarks/accelerator_benefit/power/generate_pure_rtl_100mhz_post_impl.tcl
python benchmarks/accelerator_benefit/power/parse_power_reports.py
python benchmarks/accelerator_benefit/tools/generate_benchmark_artifacts.py
python benchmarks/accelerator_benefit/tools/check_benchmark_integrity.py
```

The benchmark-scoped Python clock model and the board match the locked Golden result for all 36 cases (`final_pred` and all four `final_mem` values). The reportable board active-core metric is `profile_total_cycles - profile_input_wait_cycles`: 3,601,290 cycles, 36.0129 ms at 100 MHz, in every one of the 36 cases. The subtraction removes only upstream sample starvation and retains internal back-pressure, snapshot/final-decision work, and non-RUN control overhead. Canonical XSim gives the same active-cycle result.

Only the hand-written single-thread transaction-level **Exact C++** implementation is the native CPU inference baseline: 36/36 final predictions, 144/144 final membranes, and 1,080/1,080 Snapshot boundaries match; its measured 360-run kernel median is 1777.699800 ms. Dividing this by the hardware-counter-derived FPGA active-core latency gives 49.362862x. Historical 54.0126 ms/32.912687x values include the canonical sample gap and are not used as active-core performance.

The UART-paced raw counter interval is retained only as a transport diagnostic. Integrated-system compute latency, speedup, and energy are not inferred from it; those require preloaded input plus an independent system timer.

Power operating points are separate. The retained 0.099 W result is the 1 MHz Pure RTL vectorless estimate and is not combined with the 100 MHz active latency. The direct-100-MHz Pure RTL route met timing at WNS 0.035 ns and produced 0.183 W total, 0.085 W dynamic, and 0.097 W device-static estimates. Only this 100 MHz power is combined with the 36.0129 ms active latency, giving 0.006590360700 J/decision total and 0.003061096500 J/decision active dynamic energy as DERIVED ESTIMATES. All power values are post-implementation vectorless Vivado estimates without SAIF/VCD; physical board power remains unmeasured.
