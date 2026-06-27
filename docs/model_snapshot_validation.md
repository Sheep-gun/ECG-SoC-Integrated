# Model Snapshot Validation

## Dataset

검증 대상은 AFE+ADC output 기반 60초 ECG snapshot dataset이다. Split은 record-wise로 고정했으며, 같은 record에서 나온 snapshot이 train/validation/test에 동시에 들어가지 않도록 구성했다.

| split | segments | records |
|---|---:|---:|
| train | 480 | 43 |
| validation | 240 | 21 |
| test | 240 | 21 |

Validation과 test split의 class별 segment 수는 NSR 64, CHF 64, ARR 54, AFF 58이다. Train split은 curation 이후 NSR 127, CHF 128, ARR 109, AFF 116으로 구성됐다. Record-wise split은 train/validation/test 간 record leakage를 막기 위한 원칙이며, 최종 성능 주장은 60초 snapshot 단위 segment metric을 중심으로 해석한다.

## Metric

주요 metric은 60초 snapshot 단위 segment accuracy이다. 장시간 record 단위 판단은 향후 snapshot aggregation layer에서 별도로 정의한다.

함께 보고한 지표는 다음과 같다.

- segment accuracy
- macro-F1
- balanced accuracy
- segment confusion matrix

## Final C24 Result

| split | segment accuracy | macro-F1 | balanced accuracy |
|---|---:|---:|---:|
| train | 434/480 = 90.42% | 90.28% | 90.22% |
| validation | 219/240 = 91.25% | 91.18% | 91.34% |
| test | 193/240 = 80.42% | 80.28% | 79.99% |

## Test Segment Confusion Matrix

| Actual \ Pred | NSR | CHF | ARR | AFF |
|---|---:|---:|---:|---:|
| NSR | 50 | 12 | 2 | 0 |
| CHF | 7 | 56 | 0 | 1 |
| ARR | 14 | 2 | 34 | 4 |
| AFF | 0 | 3 | 2 | 53 |

## 해석

Model Snapshot C24는 60초 snapshot 기준 test accuracy 80.42%, macro-F1 80.28%를 달성했다. 이 결과는 60초 snapshot classifier의 성능이며, 장시간 record 전체를 한 번에 넣어 clinical diagnosis를 수행한 결과가 아니다.

최종 patient-level 시스템에서는 24~48시간 ECG stream을 60초 snapshot으로 반복 분할하고, 각 snapshot의 `pred_class`, class membrane, abnormal feature evidence를 장시간 aggregation layer에서 누적한다. 이는 Holter-style continuous ECG monitoring의 흐름에 맞춰, 짧은 ECG에서 놓칠 수 있는 intermittent abnormality를 장시간 관찰하기 위한 방향이다.
