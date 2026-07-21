# Benchmark Limitations

- FPGA core/system latency is measured with hardware cycle counters, but the last-decision core interval includes input wait caused by UART pacing; it is not the 54.0126 ms no-stall cycle-derived latency.
- Exact C++ is a single-thread hand-written transaction-level implementation with audited cadence compression; it is not a literal event-driven RTL simulation.
- The historical 32.912687x value combines measured CPU latency with cycle-derived FPGA latency and is not measured-board speedup.
- Pure RTL and integrated MicroBlaze power are separate post-implementation vectorless Vivado estimates with Medium confidence and no SAIF/VCD.
- Physical board input power was not measured; no value is presented as board power or measured energy.
- Pure RTL and integrated-system resource/power scopes are not directly equivalent.
- Live ECG still requires a 30-minute observation window even though stored-data replay completes faster.
