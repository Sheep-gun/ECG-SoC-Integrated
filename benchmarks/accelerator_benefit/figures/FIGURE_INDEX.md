# Figure Index

| Figure | Source CSV | Scope | Evidence | Limitation |
|---|---|---|---|---|
| 01_cpu_vs_rtl_latency | `benchmarks/accelerator_benefit/figures/01_cpu_vs_rtl_latency_source.csv` | CPU baselines, RTL simulation, and RTL latency | mixed, explicitly labeled | Exact C++ is the native CPU baseline; Verilator is separately labeled RTL simulation runtime. |
| 02_throughput_realtime_margin | `benchmarks/accelerator_benefit/figures/02_throughput_realtime_margin_source.csv` | Throughput and real-time margin | mixed, explicitly labeled | Stored-data processing; live final decision still needs 30 minutes. |
| 03_resource_scope | `benchmarks/accelerator_benefit/figures/03_resource_scope_source.csv` | Resource scope comparison | mixed, explicitly labeled | Scopes differ: the latter includes CPU, memory, UART, interconnect, and feeder. |
| 04_streaming_memory | `benchmarks/accelerator_benefit/figures/04_streaming_memory_source.csv` | Streaming-memory benefit | mixed, explicitly labeled | The FF upper bound includes pipeline, control, and interface state. |
| 05_power_energy_status | `benchmarks/accelerator_benefit/figures/05_power_energy_status_source.csv` | Power and energy evidence status | mixed, explicitly labeled | No estimated value is presented as measured. |
| 06_benchmark_scope_diagram | `benchmarks/accelerator_benefit/figures/06_benchmark_scope_diagram_source.csv` | Benchmark scopes remain separate | mixed, explicitly labeled | No cross-scope speedup is calculated. |
| 07_future_board_completion | `benchmarks/accelerator_benefit/figures/07_future_board_completion_source.csv` | Future board measurement completion | mixed, explicitly labeled | Pending values are never drawn as zero. |
