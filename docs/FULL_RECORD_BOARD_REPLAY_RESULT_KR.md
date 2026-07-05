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
| final_mem exact match vs full-top XSim | 4 / 4 |

## 2. Class-wise Replay 결과

| case | class | transcript | final_pred | final_mem | 판정 |
|---|---|---|---:|---|---|
| `locked_nsr_case117` | NSR | `reports/board_replay/transcripts/locked_nsr_case117_uart_full_replay.txt` | match | `29/0/1/0` | exact PASS |
| `locked_chf_case91` | CHF | `reports/board_replay/transcripts/locked_chf_case91_uart_full_replay.txt` | match | `0/29/0/1` | exact PASS |
| `locked_arr_case45` | ARR | `reports/board_replay/transcripts/locked_arr_case45_uart_full_replay.txt` | match | `7/1/21/1` | exact PASS |
| `locked_aff_case16` | AFF | `reports/board_replay/transcripts/locked_aff_case16_uart_full_replay.txt` | match | `0/0/0/30` | exact PASS |

Full-top XSim 기준 비교 요약:

- `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board_summary.md`
- `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board.csv`

## 3. 해결한 검증 이슈

이전 board replay에서는 UART/MMIO feeder가 샘플 사이에 input gap을 만들 때 일부 registered event pulse와 downstream sample-valid timing이 한 cycle 어긋나 `final_mem` vector가 direct full-top XSim과 달라졌다. RTL을 sample-indexed 의미론으로 정리하고 top-level에 processing bubble을 추가해, back-to-back XSim과 board-like input-gap XSim이 같은 final result를 내도록 맞췄다.

이후 새 bitstream/XSA/ELF를 다시 생성했고, NSR/CHF/ARR/AFF 각 1건의 30분 board replay에서 transport counter, `final_pred`, `final_mem[4]`가 full-top XSim expected와 모두 일치했다.

| 구분 | 주장 범위 |
|---|---|
| Board transport/integration | 4-class 30분 replay 수행 완료 |
| Board final class | 4/4 full-top XSim final_pred match |
| Board final membrane exactness | 4/4 full-top XSim final_mem exact match |
| 전체 final_test board batch | 미수행. class-wise 대표 4건 검증 |

## 4. 사용 산출물

| 산출물 | 경로 |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| MicroBlaze ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| PC sender | `tools/board_replay/send_full_record_uart.py` |
| Full-top XSim replay helper | `tools/board_replay/run_locked_fulltop_xsim_cases.py` |

## 5. 남은 범위

- 전체 final_test 36개 30분 case의 board batch replay는 수행하지 않았다.
- Board 전류/전력 실측은 수행하지 않았고, 전력 수치는 Vivado estimate로만 보고한다.
