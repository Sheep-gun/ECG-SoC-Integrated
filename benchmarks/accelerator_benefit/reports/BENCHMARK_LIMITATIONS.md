# Benchmark Limitations

- Active-core latency is a DERIVED subtraction of two MEASURED hardware counters, not host wall time or an independent external timing measurement.
- The counter definition removes only RUN-state input starvation; its interpretation depends on the locked RTL semantics documented in `rtl/snn_ecg_30min_final_top.v`.
- Exact C++ is a single-thread hand-written transaction-level implementation with audited cadence compression; it is not a literal event-driven RTL simulation.
- Historical 54.0126 ms/32.912687x values include canonical sample-gap cycles and are superseded for active-core performance by 36.0129 ms/49.362862x.
- Integrated-system compute latency, speedup, and energy are not measured; DDR/preload plus an independent system timer is required.
- Pure RTL and integrated MicroBlaze power are separate post-implementation vectorless Vivado estimates with Medium confidence and no SAIF/VCD.
- Physical board input power was not measured; no value is presented as board power or measured energy.
- Pure RTL and integrated-system resource/power scopes are not directly equivalent.
- Live ECG still requires a 30-minute observation window even though stored-data replay completes faster.
