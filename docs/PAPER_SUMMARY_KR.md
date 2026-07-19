# Paper Summary

## 핵심 요약

본 프로젝트는 AFE+ADC XMODEL output stream을 입력으로 받아 NSR/CHF/ARR/AFF를 분류하는 SNN-inspired ECG Classification Accelerator IP Core이다. 아날로그 flow는 MATLAB 사전설계, XMODEL-aligned LTspice 실제 schematic 검증, SystemVerilog XMODEL 구현 순서로 진행하며, 이후 signed 12-bit stream을 60초 Snapshot Readout과 30분 Final Membrane Readout에 전달한다. 이 digital repo는 전체 보고서 evidence를 연결하고 RTL/XSim/Vivado/IP-XACT/Vitis/board replay 검증을 담당한다.

동일 10초 ECG 10,000-sample의 LTspice-XMODEL ADC 비교는 MAE 0.6445 LSB, correlation 0.999518, lag 0, clipping 0이었으며 98.74%가 ±5 LSB, 99.89%가 ±10 LSB 이내였다. 이는 bit-exact 주장이 아니라 schematic과 mixed-signal 행동모델 사이의 high-correlation validation이다.

![Final system architecture](../reports/final/figures/final_system_architecture.png)

최종 locked model은 `structural_guarded_silent_aff_1008710`이다. Snapshot은 고정하고 Final Membrane만 strict record-wise train/validation 기준으로 lock했다. Locked final_test는 모델 선택이나 파라미터 탐색에 사용하지 않았고, lock 이후 1회만 평가했다.

## 최종 결과

![Final result summary](../reports/final/figures/final_result_summary.png)

| 항목 | 결과 |
|---|---:|
| Train | 61 / 68 = 89.71% |
| Validation | 32 / 32 = 100.00% |
| Final test 30분 chunk | 29 / 36 = 80.56% |
| Final test 30분 chunk macro F1 / balanced accuracy | 80.44% / 80.56% |
| Final test 30분 chunk class recall | NSR 100.00%, CHF 66.67%, ARR 77.78%, AFF 77.78% |
| Final test record-majority | 16 / 19 = 84.21% |
| Final test record-majority macro F1 / balanced accuracy | 80.80% / 88.19% |
| Final test record-majority class recall | NSR 100.00%, CHF 75.00%, ARR 77.78%, AFF 100.00% |
| Test evaluation count | 1 |
| Test used for selection | false |

Validation 100.00%는 model-selection 성능으로만 해석한다. 최종 held-out 성능은 final_test accuracy, macro F1, balanced accuracy, class별 recall을 함께 기준으로 보고한다.

## 제출 포지션

본 결과는 실제 전극 기반 의료기기 검증이 아니라, MATLAB 설계 reference, LTspice schematic, AFE+ADC XMODEL과 SNN-inspired RTL Accelerator IP Core를 signed 12-bit stream contract로 연결한 biomedical mixed-signal-to-digital FPGA prototype이다. 원본 analog 개발은 teammate repositories에서 유지하며, 보고서용 evidence mirror는 이 repo에 보존한다. 디지털 accelerator는 Python golden, XSim, Vivado implementation, IP-XACT packaging과 Vitis/MicroBlaze board replay로 검증한다.

## 한계

- Source ECG는 이미 digitized public record이다.
- AFE+ADC는 MATLAB/LTspice/XMODEL model-based verification 결과이며 상세 evidence는 `reports/final/analog_validation_result.md`에 보존한다.
- Physical AFE PCB, ADC silicon, transistor-level layout 검증은 수행하지 않았다.
- Clinical diagnosis validation은 수행하지 않았다.
- Board replay는 strict final_test 36개 30분 case 전체에 대해 수행했지만, physical analog validation은 아니며 final_pred/final_mem exact match는 모두 36/36으로 보고한다.
