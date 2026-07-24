# 36-case Board Replay Final Memory Alignment Audit

## Summary

36-case board replay에서 `CHF_chfdb_chf06_chunk19` 1개 case의 `final_pred`는 일치했지만 `final_mem` exact 비교가 1 count 어긋난 상태였다. RTL source와 packaged IP source는 동일했고, 같은 board case를 재실행해도 board final_mem은 동일하게 재현되었다.

최종 원인은 RTL arithmetic 오류가 아니라 expected 생성 조건 차이였다. 기존 expected는 `snn_ecg_30min_final_top`을 0-cycle direct sample stimulus로 구동했다. 실제 board replay는 MicroBlaze feeder/UART path를 지나므로 accepted sample 사이에 ready-valid idle gap이 존재한다.

## Resolution

Board-facing expected는 full-top RTL XSim을 `sample_gap_cycles=2`로 재생성한 값을 기준으로 고정한다. 이 조건은 board replay path의 feeder/UART ready-valid 간격을 반영하며, 기존 mismatch case의 expected final_mem을 board와 같은 값으로 만든다.

| 항목 | 결과 |
|---|---|
| Affected case | `CHF_chfdb_chf06_chunk19` |
| Previous direct 0-gap expected final_mem | `NSR=1, CHF=-3, ARR=9, AFF=33` |
| Board final_mem | `NSR=1, CHF=-3, ARR=10, AFF=32` |
| Board-equivalent XSim expected final_mem | `NSR=1, CHF=-3, ARR=10, AFF=32` |
| Final 36-case final_pred match | 36/36 |
| Final 36-case final_mem exact match | 36/36 |

## Final Artifact Source

- Board-equivalent XSim predictions: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv`
- XSim metadata: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_metadata.json`
- XSim-vs-board summary: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_xsim_vs_board_summary.md`
- 36-case manifest: `reports/final/board_replay_36_cases.csv`
- 36-case expected-vs-board CSV: `reports/final/board_replay_36_expected_vs_board.csv`
- 36-case summary: `reports/final/board_replay_36_batch_summary.md`

## Claim Boundary

이 변경은 locked RTL/bitstream의 classification 동작을 바꾼 것이 아니다. Board replay 비교 기준을 실제 board input timing에 맞춘 것이다. Label 기준 final_test chunk accuracy는 기존과 동일하게 `29/36 = 80.56%`이다.
