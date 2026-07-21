# Post-implementation Vivado Power Evidence

All three scopes use Vivado 2020.2 and `xc7a100tcsg324-1`. They are separate
post-route, vectorless estimates and must not be described as physical-board
measurements.

## Reproduction

```powershell
vivado -mode batch -source benchmarks/accelerator_benefit/power/generate_pure_rtl_post_impl.tcl
vivado -mode batch -source benchmarks/accelerator_benefit/power/generate_pure_rtl_100mhz_post_impl.tcl
vivado -mode batch -source benchmarks/accelerator_benefit/power/generate_system_post_impl.tcl
python benchmarks/accelerator_benefit/power/parse_power_reports.py
```

The original Pure RTL script recreates the low-frequency wrapper with a 100 MHz
board input and a divided 1 MHz generated core clock. The 100 MHz Pure RTL
script uses `snn_ecg_v2_nexys_a7_100mhz_top` and drives the accelerator directly
from the 100 MHz board clock, with no generated or divided core clock. The
integrated script recreates the MicroBlaze block design from the committed BD
Tcl and uses the same synthesis and implementation strategies as the immutable
board system.

The integrated Vivado work project is placed at
`%USERPROFILE%\_snn_ecg_power_mb` to stay below Vivado 2020.2's Windows path
length limit. Final reports remain in this directory tree under `results/`.
Generated projects and routed checkpoints are ignored; checkpoint SHA-256 values
are retained in `results/power_summary.json`.

## Activity and scope

No SAIF or VCD is supplied. The raw reports use Vivado default vectorless
activity propagation and report Medium confidence. `power_summary.json` is the
single source of truth used by the benchmark artifact generator. It records the
raw report hash, part, top, implementation state, clocks, activity method,
confidence, junction temperature, utilization, timing, and routed checkpoint
hash for each scope.

- Pure RTL, 1 MHz core: retained low-frequency 0.099 W estimate; no energy is
  derived with the 100 MHz board latency.
- Pure RTL, direct 100 MHz core: performance-matched accelerator power used for
  total and active-dynamic energy estimates. Timing must be MET.
- Integrated system, 100 MHz: MicroBlaze, BRAM, AXI interconnect, AXI UARTLite, sample
  feeder, interrupt logic, and accelerator.
- Physical Nexys A7 board input power: not measured; no external meter was used.
