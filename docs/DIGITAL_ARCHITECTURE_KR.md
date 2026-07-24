# SNN 기반 디지털 분류 구조

## Top hierarchy

최상위 `snn_ecg_30min_final_top`은 `u_snapshot : snn_ecg_3feat_top`과 `u_final : final_membrane_layer`를 연결한다. Snapshot timer와 제어 FSM은 top 내부 logic이며 가상의 별도 module로 표현하지 않는다.

- `u_snapshot`: 표본 사건, QRS, 리듬·파형 evidence, 60초 class membrane
- `u_final`: 30개 Snapshot 누적, margin/readout, WTA와 최종 class
- 입력: signed 12-bit ECG, sample_valid/ready, start/reset
- 출력: final_valid, final_pred_class, four Final Membrane values

## 사건과 QRS

현재 표본과 직전 표본의 차이 ΔECG를 계산하고, 변화량이 threshold를 넘으면 부호에 따라 상승·하강 Strong Event를 만든다. threshold는 각 Snapshot 초기에 관찰한 변화량 분포를 반영해 자동 설정된다.

Strong Event는 QRS LIF Neuron의 막전위에 누적된다. 발화 후 reset과 refractory period를 적용해 한 QRS가 여러 박동으로 중복 검출되는 것을 막는다.

## 리듬 evidence

- **RR Counter**: 연속 QRS 사이의 sample 수로 RR 간격을 계산한다.
- **PNN**: 현재 RR과 가장 가까운 46개 고정 기준 중 하나를 선택하고 다음 RR 예상 범위를 만든다. 실제 다음 RR과 비교해 연속 심박 간격의 규칙성을 본다.
- **RDM**: 현재와 직전 RR의 차이를 15개 수준과 비교해 4-bit 변화 코드로 만든다. PNN이 예상 적합 여부를 보는 것과 달리 RDM은 박동마다 리듬이 얼마나 크게 변했는지를 본다.
- **Ectopic Evidence**: 짧은 RR 뒤 긴 RR이 이어지는 early–late pair를 부정맥 관련 리듬 증거로 사용한다.

## 파형 evidence

네 경로는 직렬 연산이 아니라 conceptual parallel evidence group이다.

- **DSCR**: ΔECG 방향 전환 횟수로 파형 굴곡을 나타낸다.
- **RAM**: 예상 QRS 시점 주변의 짧은 관찰창에서 가장 큰 양의 표본값을 순차 비교해 peak 진폭 code를 만든다.
- **QRS MAF**: 박동 전 120 samples와 후 100 samples에서 Strong Event의 최초·최종 위치, 방향 변화와 에너지를 이용해 QRS 활동 폭과 복잡도를 만든다.
- **RBBB-like**: 예상 QRS 종료 뒤에도 Strong Event가 반복되는지를 세어 심실 내 전도 지연성 파형 대리지표를 만든다.

## 두 시간 척도 누적

각 evidence는 클래스별 signed synaptic weight에 따라 60초 Snapshot Membrane에 더해지거나 차감된다. 확정된 30개 Snapshot의 class evidence는 강도, 빈도, 반복성과 지속성을 반영해 Final Membrane에 합산된다. 입력 종료 후 four membranes를 비교해 한 class를 출력한다.

Snapshot winner의 단순 다수결이 아니다. membrane 값 자체를 장시간 누적하므로 일부 구간의 강한 evidence와 여러 구간의 반복 evidence가 함께 반영된다.

## SNN 기반이라고 부르는 이유

설계는 threshold firing, LIF membrane, refractory behavior, signed synaptic update와 multi-layer membrane accumulation을 사용한다. 따라서 본 프로젝트에서는 SNN 기반 구조로 정의한다. 다만 dense trainable SNN 전체를 학습한 모델이나 생물학적 신경계를 그대로 재현한 구조라고 주장하지 않는다.

## 하드웨어 형태

대규모 MAC array나 inference-time weight memory 없이 comparator, counter, shift/add, signed accumulator와 작은 exact lookup을 사용한다. Pure RTL 결과에서 BRAM 0, DSP 0을 달성했지만 이 수치만으로 모든 CNN/RNN보다 전력·면적이 우수하다고 일반화하지 않는다.
