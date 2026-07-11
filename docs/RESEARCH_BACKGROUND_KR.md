# 연구 배경

## 1. 장시간 ECG와 wearable 맥락

휴대형·wearable 단일유도 ECG는 일상 환경에서 ECG 파형을 기록하고 리듬 정보를 제공할 수 있다. 대표적인 소비자 ECG 기능의 규제 문서는 classifiable waveform에서 sinus rhythm과 atrial fibrillation을 구분하고, 판정할 수 없는 경우 inconclusive 결과를 제공하는 기능 범위를 설명한다. 동시에 해당 출력은 전통적 진단을 대체하지 않는다고 명시한다 [EXT-001]. 본 문서는 이 사실을 제품 성능 비교가 아니라, ECG 리듬 screening의 실용적 수요와 기능 범위를 보여주는 배경으로만 사용한다.

Ambulatory ECG에서는 증상의 발생 빈도와 관찰 목적에 따라 24/48시간 Holter 또는 더 긴 감시 방식이 선택될 수 있다 [EXT-002]. 장시간 신호에는 한 시점의 파형뿐 아니라 리듬의 지속, 반복, 간헐적 변화가 함께 존재한다. 따라서 짧은 구간의 국소 evidence와 긴 구간의 persistence를 분리해 관찰하고 다시 결합하는 구조가 공학적으로 의미가 있다.

## 2. 기존 기능 범위와 본 연구 문제의 차이

대표 소비자 ECG 기능은 제품별 독점 조건에서 AF/sinus 중심의 rhythm screening을 제공한다. 본 연구는 상용 제품을 대체하거나 임상 성능을 비교하지 않는다. 연구 문제는 공개 digitized ECG를 공통 signed 12-bit stream으로 변환한 뒤, NSR/CHF/ARR/AFF 네 public-dataset class를 장시간 다중 시간축 event/state 구조로 분류하고 RTL IP로 구현하는 것이다.

두 평가의 대상, 데이터 구성, recording 조건, label 정의와 intended use가 다르므로 정확도 수치를 직접 비교할 수 없다. 특히 본 연구의 CHF는 chfdb에서 유래한 source-dataset label이며, ARR은 광범위한 arrhythmia-labelled 범주이다.

## 3. 데이터 출처

본 평가의 class별 원천은 다음과 같다.

| Class | 원천 데이터베이스 | 등록 출처 |
|---|---|---|
| NSR | MIT-BIH Normal Sinus Rhythm Database | EXT-003 |
| CHF | BIDMC Congestive Heart Failure Database | EXT-004 |
| ARR | MIT-BIH Arrhythmia Database | EXT-005 |
| AFF | MIT-BIH Atrial Fibrillation Database | EXT-006 |

각 데이터베이스는 서로 다른 모집단·장비·sampling·recording 맥락을 가질 수 있다. 이 차이는 장시간 ECG를 제공한다는 장점과 동시에 database-class confounding이라는 중요한 한계를 만든다. 상세 방어는 `DATASET_DOMAIN_CONFOUNDING_KR.md`에 분리한다.

## 4. 설계 동기

짧은 ECG 구간은 일시적 잡음이나 모호한 morphology를 포함할 수 있고, 단일 beat만으로는 반복성과 지속성을 설명하기 어렵다. 본 설계는 beat timing, RR variability, slope/morphology, R-peak amplitude, ectopic-like pair, QRS-related evidence를 정수형 event/state로 갱신한다. 60초 Snapshot Readout은 국소 evidence를 요약하고, 30분 Final Membrane Readout은 30개 Snapshot의 signed class evidence를 누적해 최종 WTA class를 결정한다.

이는 entire 1,800,000-sample window를 모두 저장한 뒤 batch 처리하는 구조가 아니라 sample-by-sample persistent state를 갱신하는 streaming 구조이다. 연구의 핵심은 처리 속도 자체가 아니라 장시간 ECG evidence를 두 시간축으로 구조화해 투명한 RTL datapath로 구현한 점이다.

## 5. 연구 범위

본 결과는 MATLAB nominal pre-validation, SystemVerilog XMODEL model-based verification, signed-stream handoff, locked digital inference, RTL/XSim, Vivado, IP-XACT, Vitis/MicroBlaze와 FPGA replay를 연결한 semiconductor-IP engineering prototype이다. Physical AFE PCB, ADC silicon, transistor/post-layout, live electrode acquisition과 clinical validation은 범위 밖이다.

외부 출처의 서지와 URL은 `source_of_truth/external_reference_registry.csv`에 고정돼 있다. 본 문서는 상용 제품의 sensitivity/specificity 수치를 사용하지 않는다.
