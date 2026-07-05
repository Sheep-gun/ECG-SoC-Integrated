# Strict Record-wise Final Result

## Protocol

The final model is `structural_guarded_silent_aff_1008710`. Snapshot parameters are fixed, and the Final Membrane candidate was selected using train/validation only. The locked final test records were not used for model selection, parameter search, or ChatGPT context.

| Item | Result |
|---|---:|
| Train | 61 / 68 = 89.71% |
| Validation | 32 / 32 = 100.00% |
| Final test chunk | 29 / 36 = 80.56% |
| Final test record-majority | 16 / 19 = 84.21% |
| Test evaluation count | 1 |

Validation accuracy is reported as model-selection evidence only. The final generalization claim is the locked final test result.

## Evidence

- Locked records: `configs/recordwise_resplit_seed20260808/final_test_records_locked.json`
- Locked model: `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json`
- Predictions: `reports/final/strict_recordwise/final_test_predictions.csv`
- Record-majority predictions: `reports/final/strict_recordwise/structural_final_test_record_predictions.csv`
- Confusion matrix: `reports/final/strict_recordwise/structural_final_test_confusion_matrix.csv`
