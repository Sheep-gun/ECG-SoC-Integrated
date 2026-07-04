# Board Replay Final Summary

## 1. 요약

이 문서는 최종 제출 문서에 반영한 full-record board replay evidence를 요약한다.

| 항목 | 값 |
|---|---|
| 상태 | PASS |
| Case name | `test_case0_nsr` |
| Input class | NSR |
| Input samples | 1,800,000 |
| Sample rate | 1 kSPS |
| Duration | 30 min |
| Board flow | Vitis/MicroBlaze + UART chunk-ACK + AXI sample feeder |
| Expected class | 0 (NSR) |
| Board class | 0 (NSR) |
| Final prediction match | YES |
| Final membrane match | YES |
| PASS marker | `SNN_ECG_FULL_REPLAY_BOARD_PASS` |

## 2. Final membrane comparison

| class | expected | board | match |
|---|---:|---:|---:|
| NSR | 31 | 31 | 1 |
| CHF | 0 | 0 | 1 |
| ARR | 1 | 1 | 1 |
| AFF | 0 | 0 | 1 |

## 3. Counter comparison

| metric | expected | board | match |
|---|---:|---:|---:|
| samples_received | 1,800,000 | 1,800,000 | 1 |
| samples_sent_to_ip | 1,800,000 | 1,800,000 | 1 |
| samples_accepted | 1,800,000 | 1,800,000 | 1 |
| samples_consumed | 1,800,000 | 1,800,000 | 1 |
| snapshot_count | 30 | 30 | 1 |
| decision_count | 1 | 1 | 1 |
| final_valid | 1 | 1 | 1 |
| done | 1 | 1 | 1 |
| feeder_tlast_count | 1 | 1 | 1 |
| snn_error | 0 | 0 | 1 |
| feeder_error | 0 | 0 | 1 |

## 4. Evidence paths

| artifact | path |
|---|---|
| UART transcript | `reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt` |
| Expected result JSON | `reports/board_replay/comparisons/test_case0_nsr_expected_result.json` |
| Expected-vs-board CSV | `reports/board_replay/comparisons/test_case0_nsr_expected_vs_board.csv` |
| Human-readable board summary | `reports/board_replay/comparisons/test_case0_nsr_summary.md` |
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| MicroBlaze ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |

## 5. 해석 경계

이 결과는 **1-case full-record board-level integration replay** 완료 근거이다. packaged accelerator IP, sample feeder, MicroBlaze bare-metal app, UART transfer protocol, board register readback path가 하나의 30분 ECG `.mem` stream을 끝까지 처리하고 Python/XSim expected result를 재현할 수 있음을 보여준다.

그러나 full test-split board replay batch, board-level measured power, physical AFE/ADC replay, clinical validation을 의미하지 않는다.
