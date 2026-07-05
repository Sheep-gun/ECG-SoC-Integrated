# Board Replay Result

## 요약

Vitis/MicroBlaze full-record replay flow는 locked model 기준으로 다시 빌드했고, 실제 FPGA board에서 class별 30분 record 1개씩 replay했다.

| Case | Class | Samples | Snapshots | final_pred | final_mem | Result |
|---|---|---:|---:|---:|---|---|
| `locked_nsr_case117` | NSR | 1,800,000 | 30 | 0 | 29/0/1/0 | PASS |
| `locked_chf_case91` | CHF | 1,800,000 | 30 | 1 | 0/29/0/1 | PASS |
| `locked_arr_case45` | ARR | 1,800,000 | 30 | 2 | 7/1/21/1 | PASS |
| `locked_aff_case16` | AFF | 1,800,000 | 30 | 3 | 0/0/0/30 | PASS |

4개 case 모두 full-top XSim expected와 `final_pred`, `final_mem[4]`가 일치했다.

## 근거 artifact

- Comparison CSVs: `reports/final/board_replay/locked_*_expected_vs_board.csv`
- UART transcripts: `reports/final/board_replay/locked_*_uart_full_replay.txt`
- XSim-vs-board summary CSV: `reports/final/board_replay/locked_class_cases_xsim_vs_board.csv`

## 남은 범위

이 결과는 class-wise representative full-record board replay이다. 전체 36개 final_test case의 board batch replay와 board-level current/power measurement는 수행하지 않았다.
