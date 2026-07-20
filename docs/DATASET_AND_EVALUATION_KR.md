# 데이터셋과 평가 방법

## Raw-source reconstruction policy

네 PhysioNet raw database는 public Git history에 번들하지 않는다. Version 1.0.0, DOI, records used, sample-rate metadata, official URL, ODC-By 1.0 attribution, expected SHA256와 preprocessing entry는 `datasets/dataset_manifest.yaml`, `datasets/DATASET_LICENSES.md`, `datasets/SHA256SUMS_EXPECTED.txt`에 고정한다. `tools/fetch_physionet_datasets.py`는 저장소 밖에 resume download하고 `verify_physionet_datasets.py`는 data를 변경하지 않고 missing/unexpected/hash mismatch를 JSON으로 보고한다. Locked derived `.mem`, split/evaluation 및 integration evidence는 유지한다.

## Public-dataset classes

| Class | Source DB | Engineering interpretation |
|---|---|---|
| NSR | nsrdb | Normal Sinus Rhythm-labelled ECG |
| CHF | chfdb | Congestive Heart Failure-labelled ECG |
| ARR | mitdb | Arrhythmia-labelled ECG |
| AF | afdb | Atrial Fibrillation-labelled ECG |

이 label은 현재 engineering evaluation의 target이며 동일 acquisition cohort의 네 임상 진단을 의미하지 않는다.

## 30분 공통 평가 창의 선택

프로젝트의 원래 동기는 24/48시간 Holter형 장시간 관찰을 streaming state로 처리하는 것이다. 그러나 네 클래스는 길이가 같은 단일 cohort가 아니라 서로 다른 공개 데이터베이스에서 왔고, ARR 원천인 MIT-BIH Arrhythmia Database v1.0.0은 48개의 half-hour ambulatory ECG excerpt로 구성된다. 이 excerpt들은 원래 24시간 ambulatory ECG 집합에서 선택된 자료다. 근거는 `EXT-002`, `EXT-005`와 고정 PhysioNet 페이지다.

특정 클래스에만 없는 시간을 0으로 채우거나 같은 신호를 반복하지 않고 모든 클래스에 동일한 실제 관찰 길이를 적용하기 위해 현재 공통 창은 30분으로 고정했다. 구현 조건은 `60초 Snapshot × 30개`, 1 kSPS 기준 1,800,000 samples이며 `components/digital_accelerator/configs/final_submission_locked_model.json`과 `components/digital_accelerator/reports/final/final_metrics.json`에 고정되어 있다. 이는 데이터셋 제약에 따른 공학적 비교 단위이며 30분이 임상적 24시간 Holter를 대체하거나 동등하다는 주장이 아니다. 24시간으로 확장할 때는 누적 counter 폭만 늘리는 것이 아니라 Final Membrane 문턱값과 간헐 사건의 시간 희석을 다시 검증해야 한다.

## Split protocol

Split unit은 `source_record_id`이다. 한 physical source record에서 생성된 모든 chunk는 train, validation, final-test 중 하나에만 속한다. 이 strict source-record-wise 원칙은 같은 record의 waveform characteristics가 여러 partition에 직접 중복되는 leakage를 방지한다.

Locked candidate `structural_guarded_silent_af_1008710`은 train/validation만으로 선택됐다. Final-test는 selection과 parameter search에 사용하지 않았고 lock 이후 evaluation count는 1이다. Evidence는 `components/digital_accelerator/configs/final_submission_locked_model.json`과 `reports/final/final_metrics.json`이다.

## 결과

| Partition/aggregation | Correct / total | Accuracy | Macro F1 | Interpretation |
|---|---:|---:|---:|---|
| Train | 61/68 | 89.71% | — | fitting evidence |
| Validation | 32/32 | 100.00% | — | model selection only |
| Final-test 30-minute chunk | 29/36 | 80.56% | 80.44% | primary held-out engineering result |
| Final-test record-majority | 16/19 | 84.21% | 80.80% | same final partition aggregated by record |

Chunk-level class recall은 NSR 100.00%, CHF 66.67%, ARR 77.78%, AF 77.78%다. CHF recall이 가장 낮다는 사실을 숨기지 않는다. Validation 100%를 final generalization으로 사용하지 않는다.

## Digital and board evaluation distinction

Board replay 36건의 final_pred/final_mem 36/36은 board가 XSim expected output을 재현한 비율이다. 같은 board outputs를 ground-truth label과 비교하면 29/36=80.56%다. 따라서 다음 식은 금지된다.

`hardware equivalence 36/36 ≠ classification accuracy 36/36`

## 평가 해석 한계

Record-wise split이 database identity와 class identity의 결합을 해소하지는 않는다. Database name, filename, path, record ID와 split metadata는 classifier input feature로 사용하지 않았지만, waveform 자체에 남은 domain signature가 기여했을 수 있다. 자세한 내용은 `DATASET_DOMAIN_CONFOUNDING_KR.md`를 따른다.
