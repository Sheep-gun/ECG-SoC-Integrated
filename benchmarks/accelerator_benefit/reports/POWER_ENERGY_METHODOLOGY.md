# Power and Energy Methodology

- Legacy 1 MHz Pure RTL: 0.099000 W is retained as a separate low-frequency post-implementation vectorless estimate. It is not combined with the 100 MHz active-core latency, so no energy/decision is derived from it.
- Performance-matched 100 MHz Pure RTL: total 0.183000 W, dynamic 0.085000 W, and device static 0.097000 W are post-implementation vectorless Vivado estimates. Total energy is 0.183000 W x 0.036012900 s = 0.006590360700 J/decision. Active dynamic energy is 0.085000 W x 0.036012900 s = 0.003061096500 J/decision.
- The active core latency comes from `profile_total - profile_input_wait` in each board transcript. Both operands are MEASURED 100 MHz hardware counters; the subtraction is DERIVED. It retains internal stalls and snapshot/final-decision overhead.
- Integrated system: 0.271000 W is a separate post-implementation vectorless estimate for MicroBlaze, BRAM, AXI, UART, feeder, and accelerator. Integrated compute energy is **NOT_MEASURED/NOT DERIVED** because the current BIT has neither preloaded input nor an independent system timer. Multiplying this power by the UART-paced replay interval would measure transport waiting, not integrated compute energy.
- Activity: no SAIF/VCD was supplied. All three implementation scopes use Vivado default vectorless propagation and are explicitly labeled **Post-implementation vectorless Vivado power estimate**.
- Physical board power was not measured because no external power meter was available. These values must not be described as board power or measured accelerator energy.
- CPU: N/A because no RAPL/powercap or equivalent defensible counter is available.

Runtime alone is never converted into energy-efficiency speedup.
