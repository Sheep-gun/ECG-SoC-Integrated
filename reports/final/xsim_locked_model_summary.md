# XSim Locked Model Summary

## 결과

| Check | Result |
|---|---:|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Final test cases | 36 |
| final_pred mismatch | 0 |
| final_mem mismatch | 0 |

Standalone locked final-layer XSim check는 final test split에서 Python locked model과 일치한다.

## 근거 artifact

- XSim predictions: `reports/final/xsim_locked_model_predictions.csv`
- Full-top class-wise XSim predictions: `reports/final/fulltop_xsim_locked_class_cases_predictions.csv`
- 36-case board-equivalent full-top XSim predictions: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv`
- 36-case board-equivalent full-top XSim metadata: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_metadata.json`
- 36-case full-top XSim-vs-board CSV: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_xsim_vs_board.csv`
- 36-case full-top XSim-vs-board summary: `reports/final/fulltop_xsim_final_test_36/locked_class_cases_xsim_vs_board_summary.md`
- Source summary before cleanup: `reports/final_submission/xsim_locked_model_summary.json`
