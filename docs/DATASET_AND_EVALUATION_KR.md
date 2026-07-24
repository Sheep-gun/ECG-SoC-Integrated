# 데이터 구성과 평가 방법

## 클래스와 원천 데이터

| 공개 클래스 | 원천 DB | 의미 |
|---|---|---|
| NSR | MIT-BIH Normal Sinus Rhythm Database | normal sinus rhythm-labelled record |
| CHF | BIDMC Congestive Heart Failure Database | CHF-labelled record |
| ARR | MIT-BIH Arrhythmia Database | arrhythmia-labelled record |
| AF | MIT-BIH Atrial Fibrillation Database | atrial fibrillation-labelled record |

네 클래스는 동일 병원·장비·cohort에서 수집한 자료가 아니다. 따라서 분류 결과에는 질환 차이뿐 아니라 DB별 장비, 전처리, 환자군 차이가 반영될 수 있으며 database–class confounding이 남는다.

고정 RTL의 model ID와 일부 파일명·port에는 과거 명칭 `AFF`가 남아 있다. 재현성을 위해 식별자는 보존하지만 공개 서술에서는 의학적으로 통상적인 `AF`를 사용한다.

## 30분 평가 조건

MIT-BIH Arrhythmia Database의 제공 단위가 48개의 약 30분 기록이므로 반복이나 padding 없이 모든 클래스에 동일한 실제 길이를 적용하기 위해 30분을 공통 평가 단위로 정했다. 1 kSPS 기준 1,800,000 samples이며 60초 Snapshot 30개로 구성된다.

30분은 하드웨어 처리 한계가 아니다. 동일한 순차 누적 원리를 더 긴 ECG에 적용할 수 있지만 24시간 입력에서는 threshold, state range, 장시간 희석 효과와 정확도를 다시 검증해야 한다.

## annotation 기반 데이터 구성

초기 분석에서는 원천 DB label과 beat/rhythm annotation을 함께 사용해 박동 위치, RR 간격, 조기·지연 박동, 리듬 불규칙성, 진폭, QRS 폭과 파형 굴곡 후보를 계산했다. 클래스별 분포와 분리 가능성을 비교해 PNN, RDM, Ectopic Evidence, DSCR, RAM, QRS MAF, RBBB-like에 대응하는 증거를 선정했다.

annotation은 feature 후보 선정과 데이터 품질 확인을 위한 사전 분석에 사용했다. 최종 RTL은 annotation 파일을 입력으로 받지 않으며 signed 12-bit ECG stream만으로 사건과 증거를 생성한다.

사전 분석 원본은 `analysis/feature_selection/`에 보존한다. 자세한 설명은 `docs/FEATURE_SELECTION_AND_ANNOTATION_KR.md`에 있다.

## strict source-record-wise split

한 원천 ECG record에서 여러 30분 구간을 만들 수 있다. 동일 record에서 파생한 모든 구간은 train, validation, final test 중 하나에만 포함한다. 이 원칙은 동일 환자·기록의 파형 특성이 여러 분할에 직접 중복되는 leakage를 방지한다.

구조, 가중치와 임계값은 train/validation으로 결정했다. final test는 모델 선택에 사용하지 않았고 설계 고정 후 한 번만 평가했다.

| 평가 단위 | 정답/전체 | 정확도 | Macro-F1 | 해석 |
|---|---:|---:|---:|---|
| Train chunks | 61/68 | 89.71% | — | fitting 결과 |
| Validation chunks | 32/32 | 100.00% | — | model selection 전용 |
| Locked final-test chunks | 29/36 | 80.56% | 80.44% | primary result |
| Final-test source-record majority | 16/19 | 84.21% | 80.80% | 동일 final partition의 집계 |

최종 시험 혼동행렬의 recall은 NSR 9/9, CHF 6/9, ARR 7/9, AF 7/9다. 36/36 FPGA 기능 일치는 29/36 label accuracy와 다른 지표다.

## digitized ECG의 아날로그 검증 사용

공개 ECG는 이미 ADC를 거친 디지털 기록이다. 이를 실제 환자 전극 전압을 다시 측정한 것으로 표현하지 않는다. 표본을 시간·전압축에 맞춘 PWL 자극으로 재구성해 MATLAB, LTspice와 XMODEL 사이의 전달 특성과 code 정합을 검증했다.

## 재현

원본 PhysioNet waveform은 용량과 라이선스 때문에 Git에 포함하지 않는다. version, DOI, record 목록과 checksum은 `datasets/dataset_manifest.yaml`에 있으며 `tools/fetch_physionet_datasets.py`와 `tools/verify_physionet_datasets.py`로 저장소 밖에 재구성한다.
