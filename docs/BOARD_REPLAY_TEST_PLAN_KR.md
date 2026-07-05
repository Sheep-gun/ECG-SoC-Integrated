# Board Replay Test Plan

## 1. 완료된 검증

| 항목 | 결과 |
|---|---|
| Locked bitstream/XSA/ELF rebuild | 완료 |
| FPGA board program | 완료 |
| NSR 30분 full-record replay | 완료, final_pred/final_mem exact PASS |
| CHF 30분 full-record replay | 완료, final_pred/final_mem exact PASS |
| ARR 30분 full-record replay | 완료, final_pred/final_mem exact PASS |
| AFF 30분 full-record replay | 완료, final_pred/final_mem exact PASS |

## 2. 실행 명령 형식

```powershell
python tools\board_replay\send_full_record_uart.py `
  --program `
  --uart COM8 `
  --baud 230400 `
  --ready-timeout 120 `
  --done-timeout 1200 `
  --case-name locked_nsr_case117 `
  --case-id 117 `
  --mem fullrec_afe_30min_annotation_valid_balanced\test\NSR\16786\16786_30min_w035.mem `
  --expected-result reports\board_replay\locked_expected\locked_nsr_case117_fulltop_xsim_expected_result.json
```

CHF/ARR/AFF는 같은 형식으로 `locked_chf_case91`, `locked_arr_case45`, `locked_aff_case16` case를 사용한다.

## 3. 결과 파일

| 종류 | 경로 |
|---|---|
| UART transcript | `reports/board_replay/transcripts/locked_*_uart_full_replay.txt` |
| expected-vs-board CSV | `reports/board_replay/comparisons/locked_*_expected_vs_board.csv` |
| case summary | `reports/board_replay/comparisons/locked_*_summary.md` |
| full-top XSim vs board summary | `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board_summary.md` |

## 4. 남은 검증 계획

- 전체 final_test 36개 30분 case를 board batch로 확장 replay한다.
- Board 전류/전력 실측 환경이 준비되면 Vivado estimate와 비교한다.
