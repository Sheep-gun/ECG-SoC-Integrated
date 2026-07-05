# Vivado Locked Model Metrics

## Pure RTL / Board Top

| Metric | Value |
|---|---:|
| LUT | 9719 |
| FF | 5038 |
| BRAM | 0 |
| DSP | 0 |
| WNS | 8.184 ns |
| Estimated total on-chip power | 0.099 W |

## OOC/Profile Build

| Metric | Value |
|---|---:|
| LUT | 9905 |
| FF | 5769 |
| BRAM | 0 |
| DSP | 0 |
| WNS | 0.471 ns |
| WHS | 0.190 ns |

## MicroBlaze Full-record Replay System

| Metric | Value |
|---|---:|
| LUT | 12494 |
| Slice register | 8494 |
| BRAM | 16 |
| DSP | 3 |
| Setup WNS | 0.097 ns |
| Hold WNS | 0.019 ns |
| Timing constraints met | true |

MicroBlaze system resource는 CPU, LMB/BRAM, UART, AXI interconnect, MMIO-to-AXIS sample feeder를 포함한다. 따라서 bare accelerator core resource와 직접 비교하지 않는다.

## 근거 artifact

- Final metrics JSON: `reports/final/final_metrics.json`
- MicroBlaze build summary: `results/board_replay/microblaze_full_replay/microblaze_full_replay_summary.json`
- Bitstream: `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`
- XSA: `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`
- ELF: `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf`
