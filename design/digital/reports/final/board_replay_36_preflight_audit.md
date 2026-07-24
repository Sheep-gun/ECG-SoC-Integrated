# 36-case Board Replay Preflight Audit

이 문서는 strict record-wise final_test 36개 30분 chunk를 실제 Vitis/MicroBlaze board replay로 실행하기 전 확인한 repo evidence를 정리한다.

| 항목 | 확인 결과 | 경로/값 | 비고 |
|---|---|---|---|
| final_test chunk count | 확인됨 | 36 cases, class별 9개 | `reports/final/board_replay_36_cases.csv` 생성 시 전 case 검증 |
| locked model | 확인됨 | `structural_guarded_silent_aff_1008710` | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |
| mem list source | 확인됨 | `reports/final/strict_recordwise/structural_final_test_predictions.csv` | 36개 `.mem` path를 manifest로 변환 |
| full-record mem root | 확인됨 | `fullrec_afe_30min_annotation_valid_balanced/` | 각 file 1,800,000 sample 확인 |
| expected source | 확인됨 | `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` | board consistency 기준은 full-top RTL XSim expected |
| Vitis app | 확인됨 | `vitis_apps/full_record_replay/src/main.c` | UART raw i16le chunk/ack protocol |
| bitstream/XSA | 확인됨 | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`, `.xsa` | MicroBlaze full replay system |
| MicroBlaze ELF | 확인됨 | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` | board replay app |
| UART sender | 확인됨 | `tools/board_replay/run_full_record_batch_36.py` | 36-case batch runner |
| existing board replay evidence | 확인됨 | `reports/final/board_replay/*_uart_full_replay.txt` | 기존 class-wise 4-case evidence와 36-case batch는 분리 |
| 36-case board transcripts | 확인됨 | `reports/final/board_replay_36/transcripts/*.txt` | 36개 raw UART transcript |
| 36-case comparison | 확인됨 | `reports/final/board_replay_36_expected_vs_board.csv` | final_pred 36/36, final_mem exact 36/36 |

주의: `reports/final/strict_recordwise/structural_final_test_predictions.csv`는 locked software/final-layer 평가 source이고, board-level consistency 비교에는 full-top RTL XSim output을 사용한다. 실제 board bitstream은 full-top RTL datapath를 실행하므로, board-vs-expected evidence는 full-top XSim과 비교한다.
