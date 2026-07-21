# Low-Power Intent Requirements

Do not claim retention or power-gating savings until an implementable UPF/CPF
power domain is defined. The minimum candidate architecture is:

- always-on domain: wake controller, input timestamp/FIFO status, power-state
  controller and any state that must survive a 30-minute acquisition period;
- switchable accelerator domain: sample-processing datapath, snapshot logic and
  final classifier;
- explicit isolation on every switchable-to-always-on output;
- retained registers limited to state that cannot be reconstructed from the
  sample stream or persistent memory;
- a specified save/isolate/power-off and power-on/restore/de-isolate sequence;
- defined wake latency that does not lose a 1 kS/s sample.

The final report must include normal-mode leakage, off-domain leakage,
retention-cell leakage, isolation and level-shifter leakage, power-switch area,
wake energy, wake latency and IR-drop impact. The empty fields in
`low_power_overhead_template.csv` are deliberate stage gates, not zeroes.
