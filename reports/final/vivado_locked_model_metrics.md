# Vivado Locked Model Metrics

All values below were regenerated with Vivado 2020.2 for
`xc7a100tcsg324-1`. Power is a post-implementation vectorless Vivado estimate,
not physical-board power.

## Pure RTL / Board Top

| Metric | Regenerated | Historical |
|---|---:|---:|
| LUT | 9749 | 9719 |
| FF | 5045 | 5038 |
| BRAM | 0 | 0 |
| DSP | 0 | 0 |
| WNS | 8.146 ns | 8.184 ns |
| Total On-Chip Power | 0.099 W | 0.099 W |
| Dynamic Power | 0.001 W | unavailable in prior summary |
| Device Static Power | 0.097 W | unavailable in prior summary |
| Confidence | Medium | unavailable in prior summary |

The power value was reproduced. Small LUT/FF and route-timing differences are
reported rather than forced to the historical values; they reflect a new
synthesis/place/route execution with the same RTL, part, and clock constraints.

## MicroBlaze Full-record Replay System

| Metric | Regenerated |
|---|---:|
| LUT | 12494 |
| Slice register | 8494 |
| BRAM tile | 16 |
| DSP | 3 |
| Setup WNS | 0.097 ns |
| Total On-Chip Power | 0.271 W |
| Dynamic Power | 0.173 W |
| Device Static Power | 0.098 W |
| Confidence | Medium |

This scope includes MicroBlaze, LMB/BRAM, AXI interconnect, AXI UARTLite,
interrupt logic, the sample feeder, and the SNN accelerator. It must not be
mixed with the Pure RTL accelerator scope.

## Activity and evidence

- Activity method: **Post-implementation vectorless Vivado power estimate**.
- Simulation activity file: none (`---`); no SAIF/VCD.
- Switching activity: Vivado default vectorless propagation and default
  toggle-rate assumptions, not tuned to reproduce a target value.
- Pure RTL clocks: 100 MHz input and 1 MHz generated core clock.
- Integrated-system primary clock: 100 MHz; generated BSCAN clocks are listed
  in the raw report summary.
- Physical board power: not measured; no external power meter was used.

Raw reports and hashes are indexed by
`benchmarks/accelerator_benefit/power/results/power_summary.json`.
