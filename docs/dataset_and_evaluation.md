# Dataset and Evaluation

## Record-Wise Split

최종 평가는 segment random split이 아니라 strict record-wise split을 사용합니다. 같은 record에서 잘린 segment가 train, validation, test에 동시에 들어가지 않도록 구성했습니다.

## Split 구성

- train: 400 segments, class별 100개
- validation: 160 segments, class별 40개
- test: 160 segments, class별 40개

## 평가 지표

- segment-level accuracy
- record-level accuracy
- class별 precision / recall / F1
- macro-F1
- balanced accuracy
- confusion matrix

## Test 사용 원칙

train과 validation으로 parameter를 선택하고, test는 최종 고정 모델의 1회 평가에만 사용합니다. test 결과를 보고 weight, threshold, rule을 다시 조정하지 않습니다.
