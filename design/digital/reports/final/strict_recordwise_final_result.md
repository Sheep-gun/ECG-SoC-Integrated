# Strict Record-wise Final Result

## Protocol

최종 모델은 `structural_guarded_silent_aff_1008710`이다. Snapshot parameter는 고정했고, Final Membrane candidate는 train/validation만 사용해 선택했다. Locked final test records는 model selection, parameter search, ChatGPT context에 사용하지 않았다.

| 항목 | 결과 |
|---|---:|
| Train | 61 / 68 = 89.71% |
| Validation | 32 / 32 = 100.00% |
| Final test chunk | 29 / 36 = 80.56% |
| Final test chunk macro F1 / balanced accuracy | 80.44% / 80.56% |
| Final test chunk class recall | NSR 100.00%, CHF 66.67%, ARR 77.78%, AFF 77.78% |
| Final test record-majority | 16 / 19 = 84.21% |
| Final test record-majority macro F1 / balanced accuracy | 80.80% / 88.19% |
| Final test record-majority class recall | NSR 100.00%, CHF 75.00%, ARR 77.78%, AFF 100.00% |
| Test evaluation count | 1 |

Validation accuracy는 model-selection evidence로만 보고한다. 최종 generalization claim은 locked final test 결과를 기준으로 한다.

## 근거 artifact

- Locked records: `configs/recordwise_resplit_seed20260808/final_test_records_locked.json`
- Locked model: `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json`
- Predictions: `reports/final/strict_recordwise/final_test_predictions.csv`
- Record-majority predictions: `reports/final/strict_recordwise/structural_final_test_record_predictions.csv`
- Confusion matrix: `reports/final/strict_recordwise/structural_final_test_confusion_matrix.csv`
- Metric summary: `reports/final/strict_recordwise/strict_recordwise_metric_summary.json`
- Chunk class metrics: `reports/final/strict_recordwise/final_test_chunk_class_metrics.csv`
- Record-majority class metrics: `reports/final/strict_recordwise/final_test_record_majority_class_metrics.csv`
