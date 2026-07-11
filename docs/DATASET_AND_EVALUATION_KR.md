# 데이터셋과 평가 방법

## Public-dataset classes

| Class | Source DB | Engineering interpretation |
|---|---|---|
| NSR | nsrdb | Normal Sinus Rhythm-labelled ECG |
| CHF | chfdb | Congestive Heart Failure-labelled ECG |
| ARR | mitdb | Arrhythmia-labelled ECG |
| AFF | afdb | Atrial Fibrillation-labelled ECG |

이 label은 현재 engineering evaluation의 target이며 동일 acquisition cohort의 네 임상 진단을 의미하지 않는다.

## Split protocol

Split unit은 `source_record_id`이다. 한 physical source record에서 생성된 모든 chunk는 train, validation, final-test 중 하나에만 속한다. 이 strict source-record-wise 원칙은 같은 record의 waveform characteristics가 여러 partition에 직접 중복되는 leakage를 방지한다.

Locked candidate `structural_guarded_silent_aff_1008710`은 train/validation만으로 선택됐다. Final-test는 selection과 parameter search에 사용하지 않았고 lock 이후 evaluation count는 1이다. Evidence는 `components/digital_accelerator/configs/final_submission_locked_model.json`과 `reports/final/final_metrics.json`이다.

## 결과

| Partition/aggregation | Correct / total | Accuracy | Macro F1 | Interpretation |
|---|---:|---:|---:|---|
| Train | 61/68 | 89.71% | — | fitting evidence |
| Validation | 32/32 | 100.00% | — | model selection only |
| Final-test 30-minute chunk | 29/36 | 80.56% | 80.44% | primary held-out engineering result |
| Final-test record-majority | 16/19 | 84.21% | 80.80% | same final partition aggregated by record |

Chunk-level class recall은 NSR 100.00%, CHF 66.67%, ARR 77.78%, AFF 77.78%다. CHF recall이 가장 낮다는 사실을 숨기지 않는다. Validation 100%를 final generalization으로 사용하지 않는다.

## Digital and board evaluation distinction

Board replay 36건의 final_pred/final_mem 36/36은 board가 XSim expected output을 재현한 비율이다. 같은 board outputs를 ground-truth label과 비교하면 29/36=80.56%다. 따라서 다음 식은 금지된다.

`hardware equivalence 36/36 ≠ classification accuracy 36/36`

## 평가 해석 한계

Record-wise split이 database identity와 class identity의 결합을 해소하지는 않는다. Database name, filename, path, record ID와 split metadata는 classifier input feature로 사용하지 않았지만, waveform 자체에 남은 domain signature가 기여했을 수 있다. 자세한 내용은 `DATASET_DOMAIN_CONFOUNDING_KR.md`를 따른다.
