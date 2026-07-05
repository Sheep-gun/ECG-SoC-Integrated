# Strict Record-wise Protocol

## 목표

최종 평가는 record leakage를 막는 strict record-wise protocol을 사용한다. Split unit은 `source_record_id`이며, 동일 source record에서 나온 30분 chunk가 train, validation, final_test에 동시에 들어가지 않도록 구성한다.

![Strict record-wise protocol](../reports/final/figures/strict_recordwise_protocol.png)

## Locked Model

| 항목 | 값 |
|---|---|
| Final model | `structural_guarded_silent_aff_1008710` |
| Locked params hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| Split unit | `source_record_id` |
| Test evaluation count | 1 |
| Test used for selection | false |
| Test used for parameter search | false |
| Test used for ChatGPT context | false |

Snapshot Readout은 고정되어 있고, Final Membrane 구조와 파라미터는 train/validation만 사용해 lock했다. final_test는 lock 이후 1회 평가에만 사용했다.

## Result Interpretation

![Final result summary](../reports/final/figures/final_result_summary.png)

| Split | 정답 / 전체 | 정확도 | 해석 |
|---|---:|---:|---|
| Train | 61 / 68 | 89.71% | model fitting 확인 |
| Validation | 32 / 32 | 100.00% | model selection only |
| Final test 30분 chunk | 29 / 36 | 80.56% | locked held-out 평가 |
| Final test record-majority | 16 / 19 | 84.21% | record 단위 집계 평가 |

Validation 100.00%는 최종 일반화 성능으로 쓰지 않는다. 최종 성능 주장은 final_test 30분 chunk 80.56%와 record-majority 84.21%를 기준으로 한다.

## Source Artifacts

| Artifact | Path |
|---|---|
| Locked final_test records | `configs/recordwise_resplit_seed20260808/final_test_records_locked.json` |
| Locked Final Membrane params | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |
| Split metadata | `configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json` |
| Final metrics | `reports/final/final_metrics.json` |
| Final predictions | `reports/final/strict_recordwise/structural_final_test_predictions.csv` |
| Record predictions | `reports/final/strict_recordwise/structural_final_test_record_predictions.csv` |
| Confusion matrix | `reports/final/strict_recordwise/structural_final_test_confusion_matrix.csv` |
