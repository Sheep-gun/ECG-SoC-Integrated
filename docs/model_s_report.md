# Model S 최종 보고서

## 개요

Model S는 ECG stream을 직접 처리하는 SNN-inspired 4-class RTL classifier입니다. 입력은 1 kSPS signed 12-bit `adc_data`이며, QRS LIF detector와 여러 spike feature를 거쳐 NSR, CHF, ARR, AFF 중 하나를 선택합니다.

최종 모델은 Model A+에 EERG를 추가한 구조입니다.

~~~text
Model S = Model A+ + EERG
Model A+ = Model A + RBBB QRS Delay Bank
~~~

## 최종 성능

| split | segment accuracy | record accuracy | macro-F1 | balanced accuracy |
|---|---:|---:|---:|---:|
| train | 78.25% | 82.00% | 78.19% | 78.25% |
| validation | 85.00% | 90.00% | 84.91% | 85.00% |
| test | 81.88% | 94.74% | 81.93% | 81.88% |

## 해석

초기 segment random split 성능이 아니라, record-wise holdout 기준 성능을 최종 기준으로 사용합니다. 같은 record에서 나온 segment가 train, validation, test에 동시에 들어가지 않도록 하여 leakage를 줄였습니다.

ARR class는 RBBB-like conduction delay, PVC-heavy ventricular ectopic, episodic ectopic 형태가 섞인 heterogenous class입니다. 따라서 Model S는 rhythm feature만으로 ARR을 판단하지 않고 RBBB evidence와 EERG를 함께 사용합니다.
