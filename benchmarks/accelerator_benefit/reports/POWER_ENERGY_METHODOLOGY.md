# Power and Energy Methodology

- Pure RTL: 0.099 W is a Vivado estimate, not board-measured power. Estimated energy is exactly labeled **Vivado-estimated power × cycle-derived stored-data processing latency**: 0.099 W × 0.054012600 s = 0.005347247400 J/decision.
- Physical board: PENDING_BOARD. Use a calibrated bench supply or inline USB power analyzer at the board power input. Record instrument model/range/accuracy, sample interval no slower than 1 s, ambient conditions, and cable configuration. Measure at least 60 s of programmed idle power, then active continuous 36-case replay power. Report mean, standard deviation, instrument accuracy, and active-minus-idle power. This is board-level scope, not accelerator-core power.
- CPU: N/A because no RAPL/powercap or equivalent defensible counter is available and the exact CPU baseline failed equivalence.

Runtime alone is never converted into energy-efficiency speedup.
