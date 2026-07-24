# 시스템 개요

## 목적

본 설계는 장시간 ECG에서 간헐적으로 나타나는 질환 관련 구간을 놓치지 않으면서 입력 기록을 NSR, CHF, ARR, AF 중 하나로 분류하는 SNN 기반 스트리밍 가속기 IP다. 현재 30분 입력은 공개 데이터베이스에서 네 클래스를 동일 조건으로 평가하기 위한 구현·검증 단위이며, 24시간 이상 Holter 처리는 향후 확장 목표다.

## 전체 흐름

```text
Public digitized ECG
  → PWL voltage reconstruction
  → MATLAB nominal AFE/ADC design
  → LTspice circuit simulation
  → SystemVerilog XMODEL
  → 1 kSPS signed 12-bit stream
  → event, beat, rhythm and morphology evidence
  → 60 s Snapshot Membrane
  → 30-Snapshot Final Membrane
  → NSR / CHF / ARR / AF
  → AXI IP / MicroBlaze / FPGA replay
```

## 아날로그부

AFE는 약 0.5–150 Hz ECG 대역을 형성하고 60 Hz 전원선 성분을 억제한다. 공개 ECG는 이미 digitized된 기록이므로 시간축과 전압축을 맞춘 PWL 자극으로 재구성한다. MATLAB에서 공칭 전달 특성을 정한 뒤 LTspice AFE, S/H, ADC와 SystemVerilog XMODEL로 단계별 정합을 확인한다.

## 디지털부

표본 차이에서 Strong Event를 만들고 QRS LIF Neuron으로 박동 후보를 검출한다. 리듬 경로는 PNN, RDM, Ectopic Evidence를, 파형 경로는 DSCR, RAM, QRS MAF, RBBB-like를 사용한다. 각 사건은 클래스별 signed evidence로 변환되어 Snapshot과 Final Membrane에 누적된다.

60초 Snapshot과 30분 Final Membrane 자체가 연구의 목적은 아니다. 핵심은 제한된 Window를 순차 처리하면서 일부 구간의 강한 질환 증거와 여러 구간에 걸친 반복성·지속성을 함께 반영하는 계층형 장시간 판정이다.

## 구현부

Pure RTL은 AXI-Lite 제어·결과 레지스터와 AXI-Stream 입력을 갖는 IP로 패키징된다. MicroBlaze는 시작과 결과 확인을, Sample Feeder는 signed 12-bit 표본 공급을 담당한다. 완료 시 done과 IRQ가 발생하고 결과는 UART로 전송된다.

## 현재 검증 경계

- 실제 입력 길이: 30분, 1,800,000 samples
- Snapshot: 60초, 60,000 samples, 총 30개
- 분류 결과: 29/36, 정확도 80.56%, Macro-F1 80.44%
- FPGA 등가성: class 36/36, four membranes 144/144
- 미검증: physical AFE/ADC, ASIC/post-layout, clinical validation, actual 24-hour accuracy/time/power
