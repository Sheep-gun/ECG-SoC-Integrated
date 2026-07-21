# Power and Energy Methodology

- Pure RTL: 0.099000 W is a post-implementation vectorless Vivado estimate, not board-measured power. Derived energy is **estimated power x hardware-counter-derived active core latency**: 0.099000 W x 0.036012900 s = 0.003565277100 J/decision.
- The active core latency comes from `profile_total - profile_input_wait` in each board transcript. Both operands are MEASURED 100 MHz hardware counters; the subtraction is DERIVED. It retains internal stalls and snapshot/final-decision overhead.
- Integrated system: 0.271000 W is a separate post-implementation vectorless estimate for MicroBlaze, BRAM, AXI, UART, feeder, and accelerator. Integrated compute energy is **NOT_MEASURED/NOT DERIVED** because the current BIT has neither preloaded input nor an independent system timer. Multiplying this power by the UART-paced replay interval would measure transport waiting, not integrated compute energy.
- Activity: no SAIF/VCD was supplied. Both results use Vivado default vectorless propagation and are explicitly labeled **Post-implementation vectorless Vivado power estimate**.
- Physical board power was not measured because no external power meter was available. These values must not be described as board power or measured accelerator energy.
- CPU: N/A because no RAPL/powercap or equivalent defensible counter is available.

Runtime alone is never converted into energy-efficiency speedup.
