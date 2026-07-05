# Vivado / IP Metrics

| Metric | Value | Source |
|---|---:|---|
| locked pure RTL LUT | 9719 | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/snn_ecg_v2_vivado_summary.json` |
| locked pure RTL FF | 5038 | same |
| locked pure RTL BRAM | 0 | same |
| locked pure RTL DSP | 0 | same |
| locked pure RTL WNS ns | 8.184 | timing report |
| locked pure RTL total power W | 0.099 | power report |
| OOC/profile LUT | 9905 | `results/final_membrane_v2_snn/profile_synth_overhead/profile_synth_overhead_summary.json` |
| OOC/profile FF | 5769 | same |
| OOC/profile BRAM | 0 | same |
| OOC/profile DSP | 0 | same |
| OOC/profile WNS ns | 0.471 | same |
| MicroBlaze full replay LUT | 12485 | `results/board_replay/microblaze_full_replay/microblaze_full_replay_summary.json` |
| MicroBlaze full replay slice_reg | 8480 | same |
| MicroBlaze full replay BRAM | 16 | same |
| MicroBlaze full replay DSP | 3 | same |
| MicroBlaze full replay WNS ns | 0.294 | same |

Limitations: Vivado power is an estimate. MicroBlaze system resources include CPU/LMB/BRAM/UART/interconnect/sample-feeder infrastructure and should not be compared directly with the bare accelerator core. The locked MicroBlaze full replay flow is rebuilt through bitstream/XSA/ELF; actual locked UART replay transcript is still pending.
