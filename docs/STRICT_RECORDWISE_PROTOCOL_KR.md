# Strict Record-wise Protocol

## 목표

최종 평가는 record leakage를 막는 strict record-wise protocol을 사용한다. Split unit은 `source_record_id`이며, 동일 source record에서 나온 chunk가 train/validation/final_test에 동시에 들어가지 않도록 한다.

## Locked Model

| Item | Value |
|---|---|
| Final model | `structural_guarded_silent_aff_1008710` |
| Locked params hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| Locked records | `configs/recordwise_resplit_seed20260808/final_test_records_locked.json` |
| Locked params | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |

## Selection Boundary

| Check | Value |
|---|---|
| selected before final_test | true |
| final_test used for selection | false |
| final_test used for parameter search | false |
| final_test used for ChatGPT context | false |
| final_test evaluation count | 1 |
| validation role | model selection only |

## Final Result

| Split | Correct / Total | Accuracy |
|---|---:|---:|
| Train | 61 / 68 | 89.71% |
| Validation | 32 / 32 | 100.00% |
| Final test chunk | 29 / 36 | 80.56% |
| Final test record-majority | 16 / 19 | 84.21% |

Validation result is not reported as final generalization. Final reporting uses locked final_test only.

## Evidence

- `reports/final/strict_recordwise_final_result.md`
- `reports/final/strict_recordwise/final_test_predictions.csv`
- `reports/final/strict_recordwise/structural_final_test_record_predictions.csv`
- `reports/final/strict_recordwise/structural_final_test_confusion_matrix.csv`
