# Figure Index

| Figure | Source CSV | Scope | Evidence | Limitation |
|---|---|---|---|---|
| 01_cpu_vs_rtl_latency | `benchmarks/accelerator_benefit/figures/01_cpu_vs_rtl_latency_source.csv` | CPU, RTL, and measured-board latency | mixed, explicitly labeled | Exact C++ is the native CPU baseline; Verilator is separately labeled RTL simulation runtime. |
| 02_throughput_realtime_margin | `benchmarks/accelerator_benefit/figures/02_throughput_realtime_margin_source.csv` | FPGA active-core throughput and real-time margin | mixed, explicitly labeled | Derived from measured total/input-wait counters; live final decision still needs 30 minutes. |
| 03_resource_scope | `benchmarks/accelerator_benefit/figures/03_resource_scope_source.csv` | Post-route resource scope comparison | mixed, explicitly labeled | Parsed from separate post-route utilization reports. |
| 04_streaming_memory | `benchmarks/accelerator_benefit/figures/04_streaming_memory_source.csv` | Streaming-memory benefit | mixed, explicitly labeled | The FF upper bound includes pipeline, control, and interface state. |
| 05_power_energy_status | `benchmarks/accelerator_benefit/figures/05_power_energy_status_source.csv` | Clock-matched estimated power and energy | mixed, explicitly labeled | 100 MHz accelerator power is a four-class real-ECG SAIF median (ESTIMATED real-ECG SAIF); no external power meter. |
| 06_benchmark_scope_diagram | `benchmarks/accelerator_benefit/figures/06_benchmark_scope_diagram_source.csv` | Benchmark scopes remain separate | mixed, explicitly labeled | Only activity-based 100 MHz accelerator power is combined with 100 MHz active-core latency; integrated energy remains unavailable. |
| 07_future_board_completion | `benchmarks/accelerator_benefit/figures/07_future_board_completion_source.csv` | Board measurement completion | mixed, explicitly labeled | Physical board power remains unmeasured. |
| wearable_power_modes | `benchmarks/accelerator_benefit/power/results/activity_power_summary.csv` | Real-ECG SAIF burst versus literal 1 kS/s modes | ESTIMATED | About 12% routed-net SAIF match; unmatched nets vectorless; not physical board power. |
