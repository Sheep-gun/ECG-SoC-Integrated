# Figure Index

| Figure | Source CSV | Scope | Evidence | Limitation |
|---|---|---|---|---|
| 01_cpu_vs_rtl_latency | `benchmarks/accelerator_benefit/figures/01_cpu_vs_rtl_latency_source.csv` | CPU, RTL, and measured-board latency | mixed, explicitly labeled | Exact C++ is the native CPU baseline; Verilator is separately labeled RTL simulation runtime. |
| 02_throughput_realtime_margin | `benchmarks/accelerator_benefit/figures/02_throughput_realtime_margin_source.csv` | Measured-board throughput and real-time margin | mixed, explicitly labeled | Derived from measured system cycles; live final decision still needs 30 minutes. |
| 03_resource_scope | `benchmarks/accelerator_benefit/figures/03_resource_scope_source.csv` | Post-route resource scope comparison | mixed, explicitly labeled | Parsed from separate post-route utilization reports. |
| 04_streaming_memory | `benchmarks/accelerator_benefit/figures/04_streaming_memory_source.csv` | Streaming-memory benefit | mixed, explicitly labeled | The FF upper bound includes pipeline, control, and interface state. |
| 05_power_energy_status | `benchmarks/accelerator_benefit/figures/05_power_energy_status_source.csv` | Estimated power and derived energy | mixed, explicitly labeled | Post-implementation vectorless estimates; no external power meter. |
| 06_benchmark_scope_diagram | `benchmarks/accelerator_benefit/figures/06_benchmark_scope_diagram_source.csv` | Benchmark scopes remain separate | mixed, explicitly labeled | Energy is derived from estimated power times measured latency. |
| 07_future_board_completion | `benchmarks/accelerator_benefit/figures/07_future_board_completion_source.csv` | Board measurement completion | mixed, explicitly labeled | Physical board power remains unmeasured. |
