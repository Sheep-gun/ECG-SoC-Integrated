# Full-Record Board Replay Result

## 1. 최종 상태

최종 locked Final Membrane `structural_guarded_silent_aff_1008710` 기준으로 MicroBlaze full-record replay system을 다시 build하고, 새 bitstream/XSA/ELF를 사용해 FPGA board에서 30분 full-record replay를 수행했다.

| 항목 | 결과 |
|---|---|
| Bitstream/XSA/ELF rebuild | 완료 |
| Board program | 완료 |
| Class-wise 30분 replay | NSR / CHF / ARR / AFF 각 1건 수행 |
| samples_received/sent/accepted/consumed | 모든 case 1,800,000 |
| snapshot_count / decision_count | 모든 case 30 / 1 |
| done / final_valid | 모든 case 1 / 1 |
| final_pred match vs full-top XSim | 4 / 4 |
| final_mem exact match vs full-top XSim | 2 / 4 |

## 2. Class-wise Replay 결과

| case | class | transcript | final_pred | final_mem | 판정 |
|---|---|---|---:|---|---|
| `locked_nsr_case117` | NSR | `reports/board_replay/transcripts/locked_nsr_case117_uart_full_replay.txt` | match | `29/0/1/0` | exact PASS |
| `locked_chf_case91` | CHF | `reports/board_replay/transcripts/locked_chf_case91_uart_full_replay.txt` | match | board `0/29/0/1`, XSim `0/30/0/0` | final_pred PASS, final_mem mismatch |
| `locked_arr_case45` | ARR | `reports/board_replay/transcripts/locked_arr_case45_uart_full_replay.txt` | match | board `7/1/21/1`, XSim `6/4/20/0` | final_pred PASS, final_mem mismatch |
| `locked_aff_case16` | AFF | `reports/board_replay/transcripts/locked_aff_case16_uart_full_replay.txt` | match | `0/0/0/30` | exact PASS |

Full-top XSim 기준 비교 요약:

- `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board_summary.md`
- `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board.csv`

## 3. 해석

이번 replay는 MicroBlaze/UART/sample-feeder/AXI/IP 경로가 1,800,000 samples를 실제 board에서 끝까지 처리할 수 있음을 확인했다. 네 class 모두 최종 class output(`final_pred`)은 full-top XSim과 일치했다.

다만 CHF와 ARR 대표 case에서 `final_mem` vector가 full-top direct XSim과 exact로 일치하지 않았다. 보드 카운터와 error register가 모두 정상이고 final class는 맞으므로, 현재 남은 이슈는 UART/MMIO feeder의 긴 input gap이 snapshot frontend의 cycle-sensitive state에 영향을 주는지 확인하는 검증 항목이다.

즉 최종 제출 문서에는 다음처럼 구분한다.

| 구분 | 주장 범위 |
|---|---|
| Board transport/integration | 4-class 30분 replay 수행 완료 |
| Board final class | 4/4 full-top XSim final_pred match |
| Board final membrane exactness | 2/4 exact, CHF/ARR divergence 남음 |
| 남은 검증 | gap-injection XSim 또는 sample-clock-enable audit |

## 4. 사용 산출물

| 산출물 | 경로 |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| MicroBlaze ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| PC sender | `tools/board_replay/send_full_record_uart.py` |
| Full-top XSim replay helper | `tools/board_replay/run_locked_fulltop_xsim_cases.py` |

## 5. 남은 TODO

- Gap-injection XSim으로 direct XSim과 UART/MMIO board replay의 input timing 차이를 재현한다.
- Sample-indexed state가 `sample_valid/sample_fire` 기준으로만 변하는지 RTL audit을 수행한다.
- CHF/ARR final_mem exact mismatch를 해소한 뒤 class-wise replay를 재실행한다.
