# AXI Wrapper 10 ns OOC Implementation Timing

Top: `snn_ecg_axi_lite_stream_top`
Part: `xc7a100tcsg324-1`
Clock period: `10.0` ns

| PROFILE_EN | Routed | Constraints met | Setup WNS ns | Setup TNS ns | Hold WHS ns | Hold THS ns | PW WNS ns | CDC report |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | True | True | 0.081 | 0.0 | 0.098 | 0.0 | 3.75 | True |

## Worst Setup Paths

### PROFILE_EN=1

- Slack ns: `0.081`
- Source: `u_core/u_snapshot/u_dscr/filt_mem_reg[0]/C`
- Destination: `u_core/u_snapshot/u_dscr/down_mem_reg[3]/D`
- Logic levels: `19` (`CARRY4=12 LUT1=2 LUT4=1 LUT6=4`)
