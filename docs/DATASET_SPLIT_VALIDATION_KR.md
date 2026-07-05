# Strict Record-wise Dataset 및 Final Membrane 확정 프로토콜

## 1. 최종 Dataset 기준

최종 보고서에서 사용하는 record-wise 검증 기준은 `source_record_id` 단위로 train / validation / test를 분리한 strict record-wise dataset이다. 같은 ECG source record에서 나온 30분 chunk가 서로 다른 split에 들어가지 않도록 구성했고, class label을 제거한 `physical_record_id` 기준으로도 overlap이 없음을 확인한다.

| 항목 | 최종 기준 |
|---|---|
| Split seed | `20260808` |
| Split file | `reports/strict_recordwise_resplit_seed20260808/strict_recordwise_split.csv` |
| Config file | `configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json` |
| source_record_id overlap | 0 |
| physical_record_id overlap | 0 |
| class별 chunk 수 | train / validation / test = 17 / 8 / 9 |

## 2. Class별 구성

| class | train records | validation records | test records | train chunks | validation chunks | test chunks |
|---|---:|---:|---:|---:|---:|---:|
| NSR | 9 | 4 | 5 | 17 | 8 | 9 |
| CHF | 6 | 4 | 4 | 17 | 8 | 9 |
| ARR | 17 | 8 | 9 | 17 | 8 | 9 |
| AFF | 2 | 1 | 1 | 17 | 8 | 9 |

## 3. Final Membrane 확정 절차

최종 Final Membrane은 위 strict record-wise dataset을 기준으로 확정했다. 60초 Snapshot frontend는 먼저 고정하고, 30분 Final Membrane readout만 train / validation split에서 탐색했다.

```text
strict train records
-> candidate final membrane parameter grid 평가
-> ChatGPT 5.5 Pro 구조 제안 참고(final_test record/result 제외)
-> 3,000,000 structural-grid candidate 평가
-> validation split으로 최종 후보 선택
-> selected params lock
-> test split은 lock 이후 최종 1회 평가
-> 최종 보고서에는 locked final result만 기재
```

## 4. 최종 Locked Result

| 항목 | 결과 |
|---|---:|
| Selected candidate | `structural_guarded_silent_aff_1008710` |
| Passing candidates | 6,569 / 3,000,000 |
| Train | 61/68 = 89.71% |
| Validation | 32/32 = 100.00% |
| Final test evaluation count | 1 |
| Final test chunk accuracy | 29/36 = 80.56% |
| Final test macro-F1 | 80.44% |
| Final test record-majority accuracy | 16/19 = 84.21% |

## 5. 문서화 원칙

최종보고서에는 최종 채택된 strict record-wise dataset, locked Final Membrane parameter, 최종 test 결과만 남긴다.
