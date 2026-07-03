# 10 ns OOC Implementation Timing

Top: `snn_ecg_30min_final_top`
Part: `xc7a100tcsg324-1`
Clock period: `10.0` ns

| PROFILE_EN | Routed | Constraints met | Setup WNS ns | Setup TNS ns | Hold WHS ns | Hold THS ns | PW WNS ns |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | True | True | 0.044 | 0.0 | 0.05 | 0.0 | 3.75 |

## Worst Setup Paths

### PROFILE_EN=1

- Slack ns: `0.044`
- Source: `u_snapshot/u_dscr/filt_mem_reg[0]/C`
- Destination: `u_snapshot/u_dscr/sign_flip_spike_reg/D`
- Logic levels: `19` (`CARRY4=13 LUT1=2 LUT4=1 LUT6=3`)
