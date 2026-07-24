# 장시간 ECG 4-클래스 SNN 스트리밍 가속기 IP 통합 기술보고서

## 문서 기준

이 문서는 제27회 대한민국 반도체설계대전 참가신청서의 설계기술설명 내용을 공개 저장소용으로 확장한 기술 원고다. 개인정보, 서명과 신청 행정 정보는 포함하지 않는다.

고정 설계 기준은 다음과 같다.

| 구성 | 고정 기준 |
|---|---|
| Digital RTL | `c6b80de19cdcad5b7e43fe7835588b629d847f75` |
| Timing pipeline history | `c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa`, `5e2e5d0a46be47d8086b8642e055066079bfa4e6` |
| MATLAB | `907f7e1f081a9d6a5703a32095d962143315a192` |
| XMODEL | `4756a5086023547328ef44fd5fd87da3c250dc39` |
| FPGA | Artix-7 XC7A100T-CSG324-1, Vivado 2020.2 |
| Public classes | NSR, CHF, ARR, AF |
| 실제 검증 입력 | 30분, 1 kSPS, signed 12-bit |

고정 model ID와 legacy RTL port에는 `AFF`가 남아 있지만 공개 문서의 클래스 표기는 `AF`로 통일한다.

# 1. 연구 목적과 필요성

ECG는 심장의 전기 활동을 시간에 따라 기록한 전압 파형이다. 짧은 구간에서는 개별 박동의 형태를 볼 수 있지만 한 시점이 장시간 상태를 대표하지는 않는다. 대표적인 ambulatory ECG 검사인 Holter가 24시간 이상 기록하는 이유도 간헐적 이상과 리듬 변화의 반복·지속성을 포착하기 위해서다.

웨어러블 분류 코어가 장시간 원시 ECG 전체를 저장하고 dense model로 반복 분석하면 buffer, memory access와 연산 부담이 커진다. 본 설계는 필요한 사건과 분류 증거를 표본마다 갱신하고 장시간 누적하는 SNN 기반 streaming RTL을 제안한다.

연구의 핵심은 “60초와 30분”이라는 숫자 자체가 아니다. 연속 ECG를 제한된 Window로 순차 처리하면서 대부분 정상으로 보이는 기록 속의 강한 질환 관련 Window를 포착하고, Window별 증거 강도, 출현 빈도, 반복성과 장시간 지속성을 누적해 입력 기록의 클래스를 결정하는 데 있다.

최종 목표는 AFE–ADC 후단에 이식할 수 있는 저전력 분류 가속기 IP다. 현재 결과는 FPGA와 model-based analog 환경의 engineering prototype evidence이며 clinical diagnostic device 또는 fabricated ASIC이 아니다.

# 2. 관련 연구와 설계 위치

## 2.1 개별 심박 SNN

Amirshahi와 Hashemi는 R-peak 주변 개별 beat를 Poisson spike로 변환하고 STDP/R-STDP로 분류했다 [1]. Chen 등은 level-crossing ADC와 spiking CNN으로 선택한 beat를 N, SVEB, VEB, F로 분류했다 [2]. 이들은 event/SNN ECG hardware 방향을 보여주지만 여러 Window를 장시간 입력의 class로 누적하지 않는다.

## 2.2 연속 ECG 이상 검출

Bauer 등은 ECG를 asynchronous binary event로 바꾸고 recurrent SNN reservoir에서 병리 pattern의 존재 여부를 binary trigger로 출력했다 [3]. 이 연구는 “지금 평소와 다른 pattern이 있는가”를 알리는 anomaly detector다. 본 설계는 검출된 여러 구간의 evidence를 누적해 NSR, CHF, ARR, AF 중 하나를 출력한다.

## 2.3 기록과 환자 수준 통합

Shanmugam 등은 약 48시간 ECG에서 위험도가 높은 beat sequence를 집계해 patient-level cardiovascular-death risk를 예측했다 [4]. Zihlmann 등은 9–61초 ECG의 CNN feature를 평균 또는 bidirectional LSTM으로 통합해 normal, AF, other, noisy 네 class를 출력했다 [5]. 이 네 class는 본 설계의 NSR, CHF, ARR, AF와 다르다.

DeepHHF는 24시간 Holter를 30초 Window로 나누고 encoder와 Transformer head로 5년 heart-failure risk를 예측한다 [6]. Window-to-record 구조는 유사하지만 binary prognosis software model이며 RTL membrane classifier가 아니다.

## 2.4 저전력 ECG ASIC

Abubakar 등의 65 nm TNN ECG ASIC은 이상 rhythm detection에서 746 nW를, Zhang 등의 55 nm ANN ECG processor는 개별 beat 5-class에서 12.88 µW를 보고했다. 본 설계의 2.991 µW는 완전 power-gating을 가정한 산출값이므로 measured ASIC 수치와 직접적인 전력 우위를 주장하지 않는다. 차이는 주로 개별 beat 또는 짧은 rhythm event가 아니라 여러 Window evidence로 장시간 입력을 분류하는 목적에 있다.

## 2.5 제한된 차별성 표현

검토한 대표 선행연구 범위에서는 NSR, CHF, ARR, AF 입력 분류, Snapshot별 질환 evidence의 명시적 상태화, 장시간 evidence 누적, RTL/IP/FPGA 구현과 MATLAB–XMODEL–RTL 추적성을 함께 적용한 사례를 확인하지 못하였다.

이는 세계 최초 또는 동일 연구가 없다는 단정이 아니다.

# 3. 데이터 구성과 평가 protocol

## 3.1 공개 데이터베이스

| 클래스 | 원천 |
|---|---|
| NSR | MIT-BIH Normal Sinus Rhythm Database |
| CHF | BIDMC Congestive Heart Failure Database |
| ARR | MIT-BIH Arrhythmia Database |
| AF | MIT-BIH Atrial Fibrillation Database |

이 label은 public database 기반 engineering target이다. 네 클래스가 동일 acquisition cohort가 아니므로 database–class confounding이 남는다.

## 3.2 30분 공통 조건

MIT-BIH Arrhythmia Database가 약 30분 단위 48개 record를 제공하므로 반복과 padding 없이 네 클래스에 동일한 실제 길이를 적용하기 위해 30분을 공통 조건으로 정했다. 1 kSPS에서 1,800,000 samples이며 60초 Snapshot 30개로 구성된다.

30분은 하드웨어의 최대 처리 길이가 아니다. 24시간 이상으로 확장하려면 counter range, threshold, evidence dilution과 최종 정확도를 다시 검증해야 한다.

## 3.3 source-record-wise split

각 원천 record에서 여러 30분 chunk를 만들 수 있다. 같은 record에서 생성한 모든 chunk는 train, validation, final test 중 한 분할에만 속한다. 이 방식은 같은 환자·record의 파형 특성이 여러 분할에 직접 반복되는 leakage를 막는다.

구조, weight와 threshold는 train/validation으로 결정했다. final test는 model selection에 사용하지 않았고 lock 후 한 번만 평가했다.

## 3.4 annotation 기반 사전 분석

원천 DB의 beat/rhythm annotation을 사용해 RR 간격, pNN 계열 규칙성, 연속 RR 차이, early–late pair, ΔECG 방향 변화, R-peak 진폭, QRS 폭과 말단 활동 후보를 계산했다. class별 분포, 결측률과 단순 분류율을 비교하고 hardware 구현 가능성까지 고려해 최종 evidence path를 선택했다.

annotation은 후보 feature 선정과 데이터 품질 점검에 사용했으며 최종 RTL 입력에는 포함되지 않는다. RTL은 signed 12-bit ECG만 받아 자체적으로 event와 evidence를 생성한다.

# 4. 시스템과 알고리즘

## 4.1 전체 흐름

```text
digitized ECG → PWL reconstruction
→ MATLAB → LTspice AFE/S/H/ADC → XMODEL
→ signed 12-bit ECG
→ Strong Event → QRS LIF
→ rhythm and morphology evidence
→ 60 s Snapshot Membrane
→ 30-Snapshot Final Membrane
→ NSR / CHF / ARR / AF
```

## 4.2 AFE–ADC

AFE는 HPF, 3-op-amp IA, Active Twin-T 60 Hz notch, 150 Hz LPF와 buffer로 구성한다. S/H와 12-bit ADC는 ±1.65 V 범위를 1 kSPS로 변환하고 offset-binary를 signed two’s complement로 바꿔 RTL에 전달한다.

공개 ECG는 이미 digitized되어 있으므로 시간과 전압축을 맞춘 PWL 자극으로 재구성한다. 이는 환자 전극 신호를 다시 실측했다는 뜻이 아니다.

## 4.3 event와 QRS

현재 표본과 직전 표본의 차이 ΔECG를 계산한다. Snapshot 초기에 관찰한 변화량 분포로 threshold를 자동 설정하고, 이를 넘는 변화는 부호에 따라 상승·하강 Strong Event가 된다.

Strong Event는 QRS LIF Neuron 막전위에 누적된다. threshold firing 후 reset과 refractory period를 적용해 한 QRS의 중복 검출을 막는다.

## 4.4 리듬 evidence

- RR Counter: QRS 사이 samples로 RR 간격을 계산
- PNN: 현재 RR에 가장 가까운 46개 기준으로 다음 RR 예상 범위를 만들어 규칙성 평가
- RDM: 현재·직전 RR 차이를 15개 수준과 비교해 변화 크기를 4-bit code로 표현
- Ectopic Evidence: short RR 뒤 long RR이 이어지는 early–late pair 검출

PNN은 “다음 RR이 예상 범위에 드는가”를, RDM은 “박동마다 RR이 얼마나 크게 변하는가”를 본다.

## 4.5 파형 evidence

- DSCR: ΔECG 방향 전환 횟수
- RAM: 예상 QRS 주변 관찰창에서 순차 비교한 positive peak
- QRS MAF: 박동 전 120 samples와 후 100 samples의 Strong Event 폭, 방향 변화, energy
- RBBB-like: 예상 QRS 종료 뒤 남은 반복 Strong Event

RBBB-like와 Ectopic Evidence는 임상 진단이 아니라 engineering proxy다.

## 4.6 두 시간 척도 membrane

각 evidence는 class별 signed synaptic weight에 따라 60초 Snapshot Membrane에 더해지거나 차감된다. 확정된 30개 Snapshot의 class evidence는 강도, 빈도, 반복성과 지속성을 반영해 Final Membrane에 합산된다. 입력 종료 후 four membranes를 비교해 class를 출력한다.

Snapshot winner를 세는 단순 majority vote가 아니다.

## 4.7 SNN과 hardware mapping

Threshold firing, LIF membrane, refractory behavior, signed synaptic update와 multi-layer membrane accumulation을 사용하므로 SNN 기반 구조로 정의한다.

Dense MAC array와 inference-time tensor memory 대신 comparator, counter, shift/add, signed accumulator와 exact lookup을 사용한다. 전체 30분 raw input buffer는 두지 않는다.

# 5. RTL/IP와 FPGA 구현

## 5.1 hierarchy

`snn_ecg_30min_final_top`은 `u_snapshot : snn_ecg_3feat_top`과 `u_final : final_membrane_layer`를 연결한다. Snapshot timer와 FSM은 top 내부 logic이다.

## 5.2 AXI IP

Pure RTL은 AXI-Lite control/result와 AXI-Stream ECG input을 갖는 IP로 패키징했다. MicroBlaze는 start/result를, Sample Feeder는 input stream을 담당한다. 완료 시 done/IRQ를 발생시키고 UART로 결과를 보낸다.

## 5.3 최종 implementation

| 범위 | LUT | FF | BRAM | DSP | WNS |
|---|---:|---:|---:|---:|---:|
| Pure RTL | 9,719 | 5,038 | 0 | 0 | 8.184 ns |
| MicroBlaze system | 12,494 | 8,494 | 16 | 3 | 0.097 ns |

MicroBlaze system의 BRAM과 DSP는 processor, memory와 peripheral 자원이다.

# 6. 검증

## 6.1 MATLAB–LTspice

LTspice 결과는 HPF 0.481174 Hz, IA gain 200.594 V/V, 60 Hz attenuation −83.557 dB, LPF 150.211 Hz와 clipping 0을 기록했다. MATLAB 공칭 설계와 LTspice AC sweep에서 목표 ECG band와 notch 동작을 확인했다.

## 6.2 LTspice–XMODEL

동일 10초 ECG, 10,000 samples 비교 결과는 다음과 같다.

| metric | result |
|---|---:|
| mean error | +0.0221 LSB |
| MAE | 0.6445 LSB |
| RMS | 1.3020 LSB |
| correlation | 0.999518 |
| lag | 0 sample |
| within ±1 LSB | 91.19% |
| within ±5 LSB | 98.74% |
| within ±10 LSB | 99.89% |
| maximum error | 13 LSB |
| clipping | 0 |

Model-to-model 정합이며 physical analog measurement가 아니다.

## 6.3 Python/Exact C++–RTL

- Python–RTL: class 36/36, Final Membrane 144/144
- Exact C++–RTL: integer operations 793,595/793,595
- module microtrace: 18/18
- sample state: 240,000/240,000
- Snapshot boundary: 1,080/1,080
- full-top: 36/36, each 1,800,000 accepted samples, 30 Snapshots, one decision

## 6.4 AFE–RTL acceptance

Compact 36-case evidence는 AFE-generated chunk와 digital replay input의 SHA-256 36/36 동일성 및 canonical `sample_gap_cycles=2`에서 class 36/36, membranes 144/144를 기록한다.

별도의 raw accepted-dump 감사에서는 현재 보존된 four full-30분 XMODEL files만 재실행했다. four files는 각각 1,800,000 samples, 30 Snapshots, one decision을 만들었고 class 4/4와 membranes 16/16이 직접 통합 결과와 bit-exact였다. 나머지 32 raw dumps는 현재 저장소에 없어 재생성 environment가 필요하다.

두 evidence의 범위를 혼합하지 않는다.

## 6.5 AXI와 FPGA

AXI-Lite registers, AXI-Stream backpressure/TLAST, done과 IRQ를 XSim으로 검증했다. Nexys A7-100T에서 final-test 36개를 replay한 결과 UART class 36/36과 four membranes 144/144가 XSim과 일치했다.

이 36/36은 implementation equivalence이고 label accuracy는 29/36이다.

# 7. 분류 결과

| 평가 | 결과 |
|---|---:|
| Train | 61/68, 89.71% |
| Validation | 32/32, 100.00% |
| Locked final-test chunk | 29/36, 80.56%, Macro-F1 80.44% |
| Final-test record-majority | 16/19, 84.21%, Macro-F1 80.80% |

Validation은 model selection split이며 final generalization으로 사용하지 않는다. 최종 recall은 NSR 9/9, CHF 6/9, ARR 7/9, AF 7/9다. CHF–AF와 일부 불규칙 rhythm 구분은 후속 개선 대상이다.

# 8. RTL timing bottleneck 해결

초기 주요 critical path는 `class_score_neurons`의 `rdm_level_spike → pred_class`였다. 약 90 logic levels와 52 CARRY4를 포함한 긴 accumulation, comparison, WTA path였고 `class_score_neurons`가 주요 resource/timing hotspot이었다.

Clock target을 느슨하게 하지 않고 다음과 같이 구조 분할했다.

- C24/global readout과 class WTA 분리
- `segment_done`의 `*_next` counter capture
- C24 event/gate/score delta 등록
- RDM/RAM arithmetic을 exact lookup으로 변경
- Snapshot update–adjust–commit 분리
- RBBB gate 평가 시점 정렬
- QRS MAF combinational scan을 timestamp FIFO 기반 multi-cycle 처리로 변경
- PNN predictor center 등록과 case lookup
- Final Membrane margin/WTA pairwise stage
- ARR scale/commit과 post-segment flush 정렬

검증 순서는 **critical path 관측 → pipeline 분할 → timing 재검증 → 기능 등가성 확인**이었다. 기존 RDM-to-prediction path를 제거하고 Python/RTL과 FPGA 결과를 유지하면서 최종 timing closure를 달성했다.

최적화 전 약 17.5k LUT는 historical OOC hotspot이고 최종 9,719 LUT와 범위가 달라 직접 감소율로 비교하지 않는다.

# 9. 가속 성능과 전력

## 9.1 활성시간

| 구현 | time |
|---|---:|
| Exact C++ single-thread kernel median | 1,777.6998 ms |
| FPGA core active time | 36.0129 ms |
| ratio | 49.36× |

FPGA active time은 3,601,290 cycles @100 MHz이며 input wait를 제외하고 snapshot/final work와 1,320 control overhead cycles를 포함한다. UART-paced interval은 accelerator speedup에 사용하지 않는다.

## 9.2 power estimate

| scenario | result |
|---|---:|
| continuous 1 kSPS allocation | 142.0 mW |
| 100 MHz burst allocation | 149.5 mW |
| active energy per 30-minute decision | 5.3839 mJ |
| ideal complete power-gated average | 2.991 µW |

[
E_{active}=149.5\,\mathrm{mW}\times36.0129\,\mathrm{ms}=5.3839\,\mathrm{mJ}
]

[
P_{avg,ideal}=\frac{5.3839\,\mathrm{mJ}}{1800\,\mathrm{s}}=2.991\,\mathrm{\mu W}
]

2.991 µW는 off leakage, retention, isolation, wake와 data movement cost를 0으로 둔 이상적 산출값이다. FPGA board input power와 ASIC silicon power를 측정하지 않았다.

# 10. 기여와 한계

## 10.1 기여

- 장시간 ECG를 Window evidence와 Final Membrane으로 연결하는 multi-timescale SNN 구조
- annotation 기반 사전 분석에서 선택한 해석 가능한 rhythm/morphology evidence
- raw input window를 저장하지 않는 streaming integer RTL
- BRAM 0, DSP 0 Pure RTL과 timing closure
- MATLAB, LTspice, XMODEL, Python, Exact C++, RTL/XSim, AXI, MicroBlaze와 FPGA traceability
- critical-path observation부터 functional equivalence까지 남긴 timing optimization history

## 10.2 한계

- 실제 검증 input은 30분
- 24시간 accuracy, latency와 power 미검증
- database–class confounding
- raw full-30분 XMODEL dump archive는 4/36
- physical AFE PCB, ADC silicon 미제작
- ASIC/post-layout, silicon power 미검증
- clinical validation 미수행
- 2.991 µW는 ideal power-gating 산출

# 11. 재현성과 저장소 구조

설계 원본은 `design/`, equivalent model은 `models/`, Vivado project는 `vivado/`, 검증 근거는 `verification/`, claim과 commit은 `project_registry/`에 분리한다. 정확한 실행 순서는 `REPRODUCIBILITY_KR.md`에 있다.

최종 tree는 Pure RTL과 MicroBlaze 두 Vivado project만 유지하고 temporary packaging/catalog project, duplicated upstream copy, private submission과 raw PhysioNet data를 제외한다.

# 참고문헌

1. A. Amirshahi and M. Hashemi, “ECG Classification Algorithm Based on STDP and R-STDP Neural Networks for Real-Time Monitoring on Ultra Low-Power Personal Wearable Devices,” IEEE TBCAS, 2019. https://doi.org/10.1109/TBCAS.2019.2948920
2. J. Chen et al., “An Event-Driven Compressive Neuromorphic System for Cardiac Arrhythmia Detection,” IEEE ISCAS, 2022. https://ieeexplore.ieee.org/document/9937756/
3. F. C. Bauer, D. R. Muir, and G. Indiveri, “Real-Time Ultra-Low Power ECG Anomaly Detection Using an Event-Driven Neuromorphic Processor,” IEEE TBCAS, 2019. https://doi.org/10.1109/TBCAS.2019.2953001
4. D. Shanmugam, D. Blalock, and J. Guttag, “Multiple Instance Learning for ECG Risk Stratification,” MLHC, 2019. https://proceedings.mlr.press/v106/shanmugam19a.html
5. M. Zihlmann, D. Perekrestenko, and M. Tschannen, “Convolutional Recurrent Neural Networks for Electrocardiogram Classification,” Computing in Cardiology, 2017. https://doi.org/10.22489/CinC.2017.070-060
6. E. Zvuloni et al., “Modeling day-long ECG signals to predict heart failure risk with explainable AI,” npj Digital Medicine, 2026. https://doi.org/10.1038/s41746-026-02835-8
7. A. Abubakar et al., “A 746 nW ECG Processor ASIC Based on Ternary Neural Network,” IEEE TBCAS, 2022. https://doi.org/10.1109/TBCAS.2022.3196059
8. C. Zhang et al., “A Low-Power ECG Processor ASIC Based on an Artificial Neural Network for Arrhythmia Detection,” Applied Sciences, 2023. https://doi.org/10.3390/app13179591
