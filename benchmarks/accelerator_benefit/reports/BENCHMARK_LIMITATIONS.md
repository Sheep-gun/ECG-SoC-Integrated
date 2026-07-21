# Benchmark Limitations

- Active-core latency is a DERIVED subtraction of two MEASURED hardware counters, not host wall time or an independent external timing measurement.
- The counter definition removes only RUN-state input starvation; its interpretation depends on the locked RTL semantics documented in `rtl/snn_ecg_30min_final_top.v`.
- Exact C++ is a single-thread hand-written transaction-level implementation with audited cadence compression; it is not a literal event-driven RTL simulation.
- Historical 54.0126 ms/32.912687x values include canonical sample-gap cycles and are superseded for active-core performance by 36.0129 ms/49.362862x.
- Integrated-system compute latency, speedup, and energy are not measured; DDR/preload plus an independent system timer is required.
- The 1 MHz Pure RTL and integrated MicroBlaze results remain separate vectorless Vivado estimates. The reportable direct-100-MHz accelerator result uses four real-ECG burst SAIF traces, but only about 12% of routed nets match; unmatched nets retain vectorless propagation and confidence is Medium.
- The 1 MHz 0.099 W result must not be multiplied by the 100 MHz active-core latency; the former mixed-clock energy value is invalidated.
- Physical board input power was not measured; no value is presented as board power or measured energy.
- Pure RTL and integrated-system resource/power scopes are not directly equivalent.
- Literal 1 kS/s and preloaded-burst modes are separated, but the 1 kS/s SAIF traces cover a 100-sample prefix rather than a full 30-minute record.
- The valid timing-closed FPGA boundary includes the board-harness clocking context. Standalone accelerator-only 100 MHz routes failed timing and their power values are excluded.
- The 55/65/28 nm ASIC claim is blocked because no target PDK, Liberty/LEF, or signoff-capable ASIC toolchain is installed; no FPGA number is presented as ASIC PPA.
- The wearable budget is intentionally incomplete until sample memory, MCU, BLE, PMIC, retention/isolation, wake energy, and off-state leakage are characterized.
- Live ECG still requires a 30-minute observation window even though stored-data replay completes faster.
