# 연구 목표

## 핵심 목표

공개 ECG 데이터에서 생성한 AFE+ADC-compatible signed 12-bit stream을 sample-by-sample으로 받아, 단기 beat·morphology evidence와 장기 persistence를 결합해 NSR, CHF, ARR, AFF 네 public-dataset class를 분류하는 streaming SNN-inspired accelerator IP를 설계하고 검증한다.

## 세부 목표

1. 장시간 ECG를 제한된 길이의 Snapshot으로 순차 처리하고, 간헐적 질환 증거의 강도·빈도·반복성과 장시간 일관성을 기록 단위 상태에 누적하는 구조를 정의한다. 현재 60초 Snapshot 30개는 공개 데이터셋 길이에 맞춘 검증 설정이다.
2. event/state update를 integer counter, comparator, signed accumulator와 fixed-size persistent state로 구현한다.
3. 전체 30분 raw input을 저장하지 않고 streaming으로 최종 decision을 생성한다.
4. MATLAB nominal intent에서 XMODEL, signed digital handoff, locked RTL까지 신호 규약을 추적한다.
5. strict source-record-wise protocol과 locked final-test를 사용해 분류 결과의 평가 경계를 고정한다.
6. XSim, Vivado implementation, IP-XACT, Vitis/MicroBlaze와 FPGA replay로 구현 사슬을 검증한다.
7. artifact hash, upstream commit, contributor ownership과 claim status를 통해 향후 보고서의 모든 핵심 문장을 방어 가능하게 만든다.

## 성공 기준

분류 목표는 locked final-test 결과를 있는 그대로 보고하고, 구현 목표는 같은 input에서 기준 모델/RTL/board가 같은 final_pred와 final_mem을 재현하는 것이다. Resource와 timing closure는 hardware feasibility evidence로 사용한다. 완료된 NO_BOARD benchmark는 구현 효과를 보조하지만 분류 구조보다 앞선 핵심 기여로 선언하지 않는다. Physical board timing·power·energy는 별도 측정 전까지 미완료다.

## 전체 연구 흐름

`public digitized ECG → MATLAB nominal AFE+ADC pre-validation → SystemVerilog AFE+ADC XMODEL verification → signed 12-bit 1 kSPS stream → 60-second Snapshot Readout → 30-minute Final Membrane Readout → NSR/CHF/ARR/AFF → RTL/XSim/Vivado/IP-XACT/Vitis/FPGA replay`
