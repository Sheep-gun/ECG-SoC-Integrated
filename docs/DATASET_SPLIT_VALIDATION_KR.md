# Dataset Split 신뢰성 검증

## 1. 왜 chunk-level split만으로는 부족한가

ECG record 하나에서 여러 30분 chunk를 잘라 train/validation/test에 나누면, 같은 source record의 rhythm/morphology 특성이 여러 split에 동시에 들어갈 수 있다. 이 경우 test accuracy는 실제 새로운 record에 대한 generalization보다 낙관적으로 보일 수 있다.

따라서 본 보강에서는 기존 chunk-level 결과를 유지하되, 그것을 strict record-wise 결과처럼 말하지 않는다. 대신 record overlap audit, record-wise regrouping stress-test, leave-one-record-out report를 별도로 제공한다.

## 2. 현재 repo split 상태

감사 스크립트:

```powershell
python tools\audit_dataset_split.py
```

결과:

- `reports/award_readiness/dataset_split_audit.md`
- `reports/award_readiness/dataset_split_audit.csv`
- `reports/award_readiness/dataset_split_leakage_detail.csv`
- `reports/award_readiness/dataset_manifest_split_trace.csv`

핵심 결과:

| class | chunks | unique records | overlapping records |
|---|---:|---:|---:|
| NSR | 34 | 18 | 15 |
| CHF | 34 | 14 | 14 |
| ARR | 34 | 34 | 0 |
| AFF | 34 | 4 | 4 |

즉 현재 30분 dataset은 class별 chunk 수를 균형화한 구조이지, strict record-wise split이 아니다.

## 3. Record-wise regrouping 결과

실행:

```powershell
python tools\run_recordwise_eval.py
```

결과 파일:

- `reports/award_readiness/recordwise_eval_summary.md`
- `reports/award_readiness/recordwise_predictions.csv`
- `reports/award_readiness/recordwise_confusion_matrix.csv`

요약:

| split | chunks | class-record pairs | correct | accuracy |
|---|---:|---:|---:|---:|
| train | 67 | 35 | 62/67 | 92.54% |
| val | 34 | 17 | 33/34 | 97.06% |
| test | 35 | 18 | 30/35 | 85.71% |

이 결과는 이미 고정된 Python golden rule set을 source-record 단위로 다시 묶어 본 stress-test이다. 모델을 새 record-wise train split에서 다시 탐색한 것은 아니므로, 독립적인 strict record-wise training protocol이라고 주장하지 않는다.

## 4. Leave-One-Record-Out 결과

실행:

```powershell
python tools\run_leave_one_record_out.py
```

결과 파일:

- `reports/award_readiness/loro_eval_summary.md`
- `reports/award_readiness/loro_predictions.csv`

class별 fixed-model localization 결과:

| class | records | chunks | correct | class recall |
|---|---:|---:|---:|---:|
| NSR | 18 | 34 | 32/34 | 94.12% |
| CHF | 14 | 34 | 32/34 | 94.12% |
| ARR | 34 | 34 | 30/34 | 88.24% |
| AFF | 4 | 34 | 31/34 | 91.18% |

AFF는 unique record가 4개뿐이므로 record diversity가 낮다. LORO 결과는 어떤 record가 취약한지 찾는 engineering audit으로 사용하고, clinical generalization claim으로 사용하지 않는다.

## 5. 보고서에 쓸 안전한 표현

사용 가능:

> 기존 88.89% test accuracy는 chunk-level balanced split 기준이다. 추가 감사에서 source record가 split을 가로지르는 항목이 확인되었으므로, 본 프로젝트는 이를 strict record-wise 결과로 주장하지 않는다. 대신 fixed-model record-wise regrouping 및 leave-one-record-out report를 추가하여 record-level 취약성을 투명하게 제시했다.

금지:

> record-wise generalization이 완전히 검증되었다.
