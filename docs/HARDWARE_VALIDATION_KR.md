# Hardware Validation

## 검증 계층

![Hardware validation flow](../reports/final/figures/hardware_validation_flow.png)

| Layer | Evidence |
|---|---|
| Python locked model | `reports/final/final_metrics.json` |
| XSim final-layer check | 36 final_test cases, final_pred/final_mem mismatch 0 |
| Pure RTL Vivado | LUT/FF/BRAM/DSP 9719/5038/0/0, WNS 8.184 ns |
| OOC/profile Vivado | LUT/FF/BRAM/DSP 9905/5769/0/0, WNS 0.471 ns |
| IP packaging | accelerator/sample-feeder `component.xml`, `xgui/*.tcl` |
| MicroBlaze build | bitstream/XSA/ELF generated, timing met |
| Board replay | NSR/CHF/ARR/AFF each 1 full 30-minute case, final_pred/final_mem exact 4/4 |

## Resource and Timing

![Resource and timing summary](../reports/final/figures/resource_timing_summary.png)

| 항목 | 결과 |
|---|---:|
| Pure RTL LUT / FF / BRAM / DSP | 9719 / 5038 / 0 / 0 |
| Pure RTL WNS | 8.184 ns |
| Pure RTL estimated total power | 0.099 W |
| OOC/profile LUT / FF / BRAM / DSP | 9905 / 5769 / 0 / 0 |
| OOC/profile WNS | 0.471 ns |
| MicroBlaze full replay LUT / FF / BRAM / DSP | 12494 / 8494 / 16 / 3 |
| MicroBlaze setup WNS / hold WNS | 0.097 ns / 0.019 ns |

MicroBlaze full replay resource는 CPU, LMB/BRAM, UARTLite, AXI interconnect, interrupt controller, MMIO-to-AXIS sample feeder, accelerator를 모두 포함한다. 따라서 pure RTL accelerator resource와 직접 비교하지 않는다.

## Board Replay

![Board replay PASS matrix](../reports/final/figures/board_replay_pass_matrix.png)

Board replay는 locked model 기준 bitstream/XSA/ELF로 수행되었다. 각 class에서 대표 30분 record 1개를 replay했으며, 각 case는 1,800,000 samples, 30 snapshots, 1 decision을 가진다.

| Case | Class | Samples | Snapshots | Result |
|---|---|---:|---:|---|
| `locked_nsr_case117` | NSR | 1,800,000 | 30 | PASS |
| `locked_chf_case91` | CHF | 1,800,000 | 30 | PASS |
| `locked_arr_case45` | ARR | 1,800,000 | 30 | PASS |
| `locked_aff_case16` | AFF | 1,800,000 | 30 | PASS |

이 결과는 class-wise representative board replay이다. 전체 final_test 36 case를 board에서 batch replay했다는 의미가 아니다.

## Source Artifacts

| Artifact | Path |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| MicroBlaze build summary | `results/board_replay/microblaze_full_replay/microblaze_full_replay_summary.json` |
| Board replay summary | `reports/final/board_replay_result.md` |
| Board replay transcripts | `reports/final/board_replay/*_uart_full_replay.txt` |
| Expected-vs-board CSVs | `reports/final/board_replay/*_expected_vs_board.csv` |
