# Python Locked Model Recheck

이 파일은 locked JSON을 다시 읽어 Python golden prediction을 재생성한 확인 결과이다.
검색/선택을 다시 수행하지 않았고, final_test evaluation counter를 증가시키지 않았다.

| 항목 | 값 |
|---|---|
| candidate | `structural_guarded_silent_aff_1008710` |
| locked_params_hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| final_test_used_for_selection | `False` |
| final_test_used_for_parameter_search | `False` |
| final_test_used_for_chatgpt_context | `False` |
| test_evaluation_count | `1` |

## Metrics

| level | correct/total | accuracy |
|---|---:|---:|
| Train | 61/68 | 89.71% |
| Validation | 32/32 | 100.00% |
| Final test chunk | 29/36 | 80.56% |
| Final test record-majority | 16/19 | 84.21% |

## Expected Artifact Match

| check | result |
|---|---|
| train | `True` |
| val | `True` |
| test | `True` |
| test_record_majority | `True` |
| test_evaluation_count | `True` |
| test_artifact_candidate | `True` |

## Outputs

- predictions: `reports\final_submission\python_locked_model_predictions.csv`
- metrics JSON: `reports\final_submission\python_locked_model_metrics.json`
- previous one-time final_test artifact: `reports\strict_recordwise_resplit_seed20260808\final_test_structural_grid_final_membrane\structural_final_test_metrics.json`
