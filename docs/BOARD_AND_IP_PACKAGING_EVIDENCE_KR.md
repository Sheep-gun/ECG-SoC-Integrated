# Board and IP Packaging Evidence

## 1. IP packaging evidence

| Evidence | Path | Status |
|---|---|---|
| AXI accelerator RTL wrapper | `rtl/axi/snn_ecg_axi_lite_stream_top.v` | Done |
| AXI4-Lite + AXI4-Stream feeder | `rtl/axi/axi_lite_axis_sample_feeder.v` | Done |
| Accelerator IP-XACT | `ip_repo/snn_ecg_axi_accelerator/component.xml` | Done |
| Accelerator xgui | `ip_repo/snn_ecg_axi_accelerator/xgui/snn_ecg_axi_accelerator_v1_0.tcl` | Done |
| Feeder IP-XACT | `ip_repo/axi_lite_axis_sample_feeder/component.xml` | Done |
| Feeder xgui | `ip_repo/axi_lite_axis_sample_feeder/xgui/axi_lite_axis_sample_feeder_v1_0.tcl` | Done |
| AXI wrapper smoke testbench | `sim/tb_snn_ecg_axi_smoke.v` | Done |
| Sample feeder smoke testbench | `sim/tb_axi_lite_axis_sample_feeder.v` | Done |

## 2. MicroBlaze smoke evidence

| Artifact | Path | Status |
|---|---|---|
| MicroBlaze smoke bitstream | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.bit` | Present |
| Smoke XSA | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.xsa` | Present |
| Block design Tcl | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke_bd.tcl` | Present |
| Address report | `results/final_membrane_v2_snn/microblaze_smoke/reports/system_bd_address.rpt` | Present |
| XSDB MMIO transcript | `results/final_membrane_v2_snn/microblaze_smoke/xsdb_mmio_transcript.txt` | PASS |
| UART C app | `sw/microblaze_smoke/src/main.c` | Source present |
| Vitis ELF | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke_app.elf` | Built |
| UART PASS transcript | `results/final_membrane_v2_snn/microblaze_smoke/uart_transcript.txt` | PASS |

MicroBlaze smoke summary:

| 항목 | 값 |
|---|---:|
| LUT / FF / BRAM / DSP | 12650 / 8746 / 16 / 3 |
| WNS / WHS | 0.185 ns / 0.037 ns |
| smoke samples | 16 |
| smoke snapshots | 2 |

BRAM/DSP는 accelerator core가 아니라 MicroBlaze/LMB/UART/system infrastructure가 포함된 system-level resource이다.

## 3. Full-record board replay evidence

Vitis MicroBlaze + UART chunk-ACK flow로 test NSR case 0의 30분 full record를 실제 board에서 replay했다.

| Artifact | Path | Status |
|---|---|---|
| Full replay bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` | Present |
| Full replay XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` | Present |
| Full replay ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` | Built |
| Full replay app source | `vitis_apps/full_record_replay/src/main.c` | Present |
| PC sender script | `tools/board_replay/send_full_record_uart.py` | Present |
| Full replay transcript | `reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt` | PASS |
| Expected-vs-board CSV | `reports/board_replay/comparisons/test_case0_nsr_expected_vs_board.csv` | PASS |
| Replay summary | `reports/board_replay/comparisons/test_case0_nsr_summary.md` | PASS |

Full replay system summary:

| 항목 | 값 |
|---|---:|
| full samples | 1,800,000 |
| snapshots per chunk | 30 |
| UART baud | 230400 |
| LUT / FF / BRAM / DSP | 12638 / 8745 / 16 / 3 |
| WNS / WHS | 0.192 ns / 0.026 ns |

Full replay result:

| 항목 | 값 |
|---|---:|
| samples_received / sent_to_ip | 1,800,000 / 1,800,000 |
| samples_accepted / consumed | 1,800,000 / 1,800,000 |
| snapshot_count / decision_count | 30 / 1 |
| final_pred | 0 |
| final_mem NSR/CHF/ARR/AFF | 31 / 0 / 1 / 0 |
| snn_error / feeder_error | 0 / 0 |

## 4. 완료 범위와 안전한 표현

현재 board-level evidence는 bitstream programming, packaged IP integration, MicroBlaze smoke system, XSDB MMIO smoke, Vitis-built ELF, UART smoke PASS transcript, test NSR case 0 full-record replay PASS transcript까지 포함한다.

다만 전체 dataset board replay batch나 physical AFE/ADC 검증이 완료된 것은 아니다. 따라서 최종 보고서에서는 다음처럼 표현한다.

> 실제 FPGA board에서 1,800,000-sample full record 1건을 MicroBlaze/UART replay로 입력하고, board final_pred/final_mem이 Python/XSim expected와 exact match함을 확인했다. 전체 test split board replay와 physical AFE/ADC validation은 향후 보완이다.

## 5. 남은 TODO

- non-NSR full-record board replay 추가
- full test split board replay batch 자동화
- AXI DMA/DDR 기반 faster replay 검토
- board-level power/current measurement
