# Post-implementation Vivado Power Evidence

Both scopes use Vivado 2020.2 and `xc7a100tcsg324-1`. They are separate
post-route, vectorless estimates and must not be described as physical-board
measurements.

## Reproduction

```powershell
vivado -mode batch -source benchmarks/accelerator_benefit/power/generate_pure_rtl_post_impl.tcl
vivado -mode batch -source benchmarks/accelerator_benefit/power/generate_system_post_impl.tcl
python benchmarks/accelerator_benefit/power/parse_power_reports.py
```

The Pure RTL script recreates the locked Nexys A7 wrapper and its 100 MHz input
plus 1 MHz generated-core constraints. The integrated script recreates the
MicroBlaze block design from the committed BD Tcl and uses the same synthesis
and implementation strategies as the immutable board system.

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

- Pure RTL: accelerator plus the locked Nexys board wrapper.
- Integrated system: MicroBlaze, BRAM, AXI interconnect, AXI UARTLite, sample
  feeder, interrupt logic, and accelerator.
- Physical Nexys A7 board input power: not measured; no external meter was used.
