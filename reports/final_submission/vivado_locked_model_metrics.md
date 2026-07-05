# Vivado Locked Model Metrics

## Pure RTL Board Top

| 항목 | 값 |
|---|---:|
| Top | `snn_ecg_v2_nexys_a7_top` |
| Part | `xc7a100tcsg324-1` |
| LUT | 9719 |
| FF | 5038 |
| BRAM | 0 |
| DSP | 0 |
| WNS | 8.184 ns |
| Estimated total on-chip power | 0.099 W |

Artifacts:

| 산출물 | 경로 |
|---|---|
| Bitstream | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/bitstream/snn_ecg_v2_nexys_a7_top.bit` |
| Timing report | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/reports/snn_ecg_v2_timing_summary.rpt` |
| Utilization report | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/reports/snn_ecg_v2_impl_utilization.rpt` |
| Power report | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/reports/snn_ecg_v2_power.rpt` |

## OOC/Profile Build

| 항목 | PROFILE_EN=1 값 |
|---|---:|
| LUT | 9905 |
| FF | 5769 |
| BRAM | 0 |
| DSP | 0 |
| WNS | 0.471 ns |
| WHS | 0.190 ns |
| `u_final` LUT / FF | 1329 / 1037 |
| `u_class` LUT / FF | 6814 / 2691 |
| PROFILE_EN overhead | +42 LUT, +708 FF |

The previous `rdm_level_spike -> pred_class` timing query now reports `No timing paths found`, which means the earlier one-cycle path has been cut by the pipeline/register boundary.

## MicroBlaze Full-Replay System Build

| 항목 | 값 |
|---|---:|
| Top | `snn_ecg_mb_full_replay_wrapper` |
| LUT | 12485 |
| Slice registers | 8480 |
| FF | 8479 |
| BRAM | 16 |
| DSP | 3 |
| WNS / WHS | 0.294 ns / 0.055 ns |
| Timing constraints | Met |
| CDC/check_timing markers | Clean |

Artifacts:

| 산출물 | 경로 |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| Bare-metal ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| Summary JSON | `results/board_replay/microblaze_full_replay/microblaze_full_replay_summary.json` |

MicroBlaze system resources include MicroBlaze, LMB/BRAM, UARTLite, interrupt/reset infrastructure, AXI interconnect, sample feeder, and the accelerator IP. They should not be compared directly with the bare accelerator resource numbers.
