# Power and Energy Methodology

- Pure RTL: 0.099000 W is a post-implementation vectorless Vivado estimate, not board-measured power. Derived energy is **estimated power x measured FPGA core-counter latency**: 0.099000 W x 187.144750920 s = 18.527330341080 J/decision.
- Integrated system: 0.271000 W is a separate post-implementation vectorless estimate for MicroBlaze, BRAM, AXI, UART, feeder, and accelerator. Derived energy is **estimated power x measured FPGA system-counter latency**: 0.271000 W x 187.144750920 s = 50.716227499320 J/decision.
- Activity: no SAIF/VCD was supplied. Both results use Vivado default vectorless propagation and are explicitly labeled **Post-implementation vectorless Vivado power estimate**.
- Physical board power was not measured because no external power meter was available. These values must not be described as board power or measured accelerator energy.
- CPU: N/A because no RAPL/powercap or equivalent defensible counter is available.

Runtime alone is never converted into energy-efficiency speedup.
