# 시스템 개요

## 프로젝트 정체성

본 프로젝트는 Holter형 장시간 ECG를 제한된 길이의 Snapshot으로 순차 처리하고, 대부분 정상으로 보이는 기록 속에서 간헐적으로 나타나는 강한 질환 증거의 강도·빈도·반복성과 장시간 일관성을 고정 폭 상태에 누적하는 SNN-inspired 기록 단위 분류 구조를 제안한다. 현재 60초 Snapshot 30개와 30분 입력은 공개 데이터셋 길이에 맞춘 구현·검증 조건이며, 구조의 본질이나 24시간 검증 완료를 뜻하지 않는다. 이 구조를 signed 12-bit streaming RTL accelerator IP로 구현·검증하였다.

## End-to-end flow

```text
PhysioNet public digitized ECG
  → MATLAB nominal AFE+ADC pre-validation
  → SystemVerilog AFE+ADC XMODEL/non-ideal verification
  → 1 kSPS signed 12-bit two's-complement stream
  → event/state feature updates
  → 60-second Snapshot Readout
  → 30-Snapshot signed Final Membrane accumulation
  → WTA: NSR / CHF / ARR / AFF
  → RTL / XSim / Vivado / IP-XACT / Vitis / FPGA replay
```

## Layer 1: MATLAB nominal pre-validation

MATLAB component는 HPF, IA gain, notch, LPF와 12-bit ADC의 nominal intent를 정의하고, frequency response, dynamic range, clipping/headroom과 signed reference vector를 검증한다. 대표 NSR/CHF/ARR/AFF 60초 record에서 clipping ratio는 모두 0%였고, 네 record의 최소 rail headroom은 약 1.0196 V였다. 이는 selected nominal model 결과이며 physical analog measurement가 아니다.

## Layer 2: XMODEL verification

SystemVerilog XMODEL component는 AFE+ADC signal chain의 non-ideal/stress 조건을 모델링하고 long signed stream을 생성한다. Emulator와 Questa/XMODEL의 36개 60초 segment 평균 RMS 차이는 1.95 LSB, lag 0으로 보고됐다. 50/60 Hz PLI, offset/wander, R/C mismatch, op-amp GBW/VOS와 ADC non-ideal 범위를 서로 다른 caveat와 함께 관리한다.

## Layer 3: Digital SNN-inspired accelerator

Digital component는 signed stream을 sample-by-sample 처리한다. Beat timing, RR variability, slope/morphology, R-peak amplitude와 ectopic/QRS-related evidence를 local event/state로 갱신하고, 60초마다 Snapshot class evidence를 만든다. Final Membrane은 30개 Snapshot의 signed evidence를 누적하고 WTA로 한 class를 출력한다.

## Layer 4: FPGA integration proof

Pure RTL implementation, AXI/IP-XACT package, MicroBlaze replay system과 FPGA board replay가 digital implementation chain을 구성한다. Board replay는 XSim expected output과 final_pred/final_mem이 36/36 일치했다. 이는 구현 functional equivalence이며 label 기준 classification accuracy는 별도의 29/36이다.

## 핵심 interface contract

| 항목 | Canonical value | Evidence |
|---|---:|---|
| sample representation | signed 12-bit two's-complement | CLM-002 |
| sample rate | 1 kSPS | CLM-002 |
| Snapshot interval | 60 s | CLM-003 |
| Final Membrane interval | 30 snapshots = 30 min | CLM-003 |
| XSim integration cadence | sample_gap_cycles=2 | CLM-013 |
| final output | class + four Final Membrane states | digital final reports |

모든 promoted metric은 `source_of_truth/global_metrics.yaml`에 evidence path, commit, owner와 limitation을 포함한다.
