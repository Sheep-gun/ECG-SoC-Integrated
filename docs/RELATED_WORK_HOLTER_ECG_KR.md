# 관련 연구와 비교 경계

정확도 순위가 아니라 **입력 시간 범위, 최종 판정 단위, 저장·연산 방식, hardware 구현**을 비교한다.

## 개별 심박 SNN

Amirshahi와 Hashemi의 *ECG Classification Algorithm Based on STDP and R-STDP Neural Networks for Real-Time Monitoring on Ultra Low-Power Personal Wearable Devices*는 R-peak 주변 개별 beat를 spike train으로 변환하고 STDP/R-STDP로 beat class를 학습한다.
DOI: https://doi.org/10.1109/TBCAS.2019.2948920

Chen 등의 *An Event-Driven Compressive Neuromorphic System for Cardiac Arrhythmia Detection*은 level-crossing ADC와 spiking CNN으로 선택한 beat를 N, SVEB, VEB, F로 분류한다.
Official: https://ieeexplore.ieee.org/document/9937756/

두 연구는 event/SNN ECG hardware 방향을 보여주지만 장시간 여러 Window를 하나의 record class로 누적하지 않는다.

## 연속 ECG 이상 검출

Bauer 등의 *Real-Time Ultra-Low Power ECG Anomaly Detection Using an Event-Driven Neuromorphic Processor*는 연속 ECG를 asynchronous event로 바꾸고 recurrent SNN reservoir에서 병리 pattern의 존재 여부를 binary trigger로 출력한다.
DOI: https://doi.org/10.1109/TBCAS.2019.2953001

이 연구는 “현재 평소와 다른 병리 pattern이 있는가”를 알린다. 본 설계는 여러 구간 evidence를 누적해 입력 기록을 NSR, CHF, ARR, AF 중 하나로 분류한다.

## 기록·환자 수준 집계

Shanmugam 등의 *Multiple Instance Learning for ECG Risk Stratification*은 약 48시간 ECG의 beat sequence 중 높은 위험 instance를 집계해 patient-level cardiovascular-death risk를 출력한다. 대부분 정상으로 보이는 긴 기록에서 중요한 일부 구간을 찾는 방향은 유사하지만 출력은 binary prognosis이고 software MIL이다.
Official: https://proceedings.mlr.press/v106/shanmugam19a.html

Zihlmann 등의 *Convolutional Recurrent Neural Networks for Electrocardiogram Classification*은 9–61초 ECG에서 CNN feature를 평균 또는 bidirectional LSTM으로 통합해 normal, AF, other, noisy 네 class를 출력한다. 본 설계의 NSR, CHF, ARR, AF와 class 정의가 같지 않으며 장시간 Holter evidence 누적이 중심이 아니다.
DOI: https://doi.org/10.22489/CinC.2017.070-060

DeepHHF의 *Modeling day-long ECG signals to predict heart failure risk with explainable AI*는 24시간 Holter를 30초 Window로 나누고 frozen encoder와 Transformer head로 5년 HF risk를 예측한다. Window-to-record 흐름은 가장 유사하지만 binary prognosis software model이며 본 설계처럼 네 public class를 RTL membrane으로 누적하지 않는다.
DOI: https://doi.org/10.1038/s41746-026-02835-8

## 저전력 ECG ASIC 비교 경계

Abubakar 등의 65 nm TNN ECG ASIC은 비정상 rhythm detection에서 746 nW를, Zhang 등의 55 nm ANN ECG processor는 개별 beat 5-class에서 12.88 µW를 보고했다. 이들은 실제 ASIC 측정 또는 해당 chip 범위의 결과이며, 본 설계의 2.991 µW는 완전 power-gating을 가정한 FPGA activity 기반 산출값이므로 직접적인 전력 우위를 주장하지 않는다.

본 설계의 차이는 주로 개별 beat·짧은 rhythm event가 아니라 여러 Window의 evidence를 누적해 30분 입력을 네 class로 분류하는 데 있다.

## 제한된 최초성 표현

검토한 대표 선행연구 범위에서는 NSR·CHF·ARR·AF 입력 분류, Snapshot별 질환 evidence의 명시적 상태화, 장시간 evidence 누적, RTL/IP/FPGA 구현과 MATLAB–XMODEL–RTL 추적성을 함께 적용한 사례를 확인하지 못하였다.

세계 최초 또는 동일한 연구가 없다는 표현은 사용하지 않는다.
