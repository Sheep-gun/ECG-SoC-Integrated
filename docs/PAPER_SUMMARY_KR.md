# Paper Summary

## 핵심 요약

본 프로젝트는 AFE+ADC XMODEL output stream을 입력으로 받아 NSR/CHF/ARR/AFF를 분류하는 SNN-inspired ECG Classification Accelerator IP Core이다. 공개 digitized ECG record를 analog-equivalent `vin`으로 재구성하고, AFE+ADC XMODEL을 거쳐 signed 12-bit stream을 만든 뒤, RTL accelerator에서 60초 Snapshot Readout과 30분 Final Membrane Readout을 수행한다.

최종 locked model은 `structural_guarded_silent_aff_1008710`이다. Snapshot은 고정하고 Final Membrane만 strict record-wise train/validation 기준으로 lock했다. Final test는 selection/search/context에 사용하지 않았고, lock 이후 한 번만 평가했다.

## 최종 결과

| Item | Result |
|---|---:|
| Train | 61/68 = 89.71% |
| Validation | 32/32 = 100.00% |
| Final test chunk | 29/36 = 80.56% |
| Final test record-majority | 16/19 = 84.21% |
| Final test evaluation count | 1 |
| XSim final_pred/final_mem mismatch | 0 / 0 |
| Board replay final_pred/final_mem match | 4/4 / 4/4 |

Validation 100%는 model-selection 결과이며 final claim은 locked final_test 결과이다.

## 최종 주장 범위

주장 가능한 것은 FPGA/VLSI engineering validation이다. 즉, AFE+ADC XMODEL-linked input generation, locked strict record-wise protocol, RTL/XSim bit-accurate check, Vivado implementation, IP-XACT packaging, Vitis/MicroBlaze class-wise board replay이다.

주장하지 않는 것은 direct electrode acquisition, physical AFE board measurement, ADC silicon measurement, transistor-level layout verification, medical diagnosis validation이다.
