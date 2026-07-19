# Limitations and Claim Boundary

## Claim Boundary

| 주장 가능 | 근거 |
|---|---|
| SNN-inspired ECG Classification Accelerator IP Core | locked protocol, RTL, AXI wrapper, IP-XACT package |
| signed 12-bit AFE+ADC XMODEL stream input compatibility | digital input contract, 1 kSPS stream, 60 s snapshot, 30 min final decision |
| MATLAB-LTspice-XMODEL model-based analog validation | nominal response, XMODEL-aligned schematic, 10초 10,000-code cross-model comparison |
| Fully blind strict record-wise locked final holdout | final_test not used for selection/search/context, evaluation count 1 |
| RTL/XSim locked-model equivalence | final_pred/final_mem mismatch 0 over 36 final_test cases |
| Vivado/IP-XACT packaged accelerator IP | timing/resource/power reports, `component.xml` artifacts |
| Vitis/MicroBlaze 36-case board replay | UART transcripts and expected-vs-board CSV for 36 strict final_test 30-minute cases |

## 주장 금지

| 주장 금지 | 이유 |
|---|---|
| Raw analog ECG acquisition | Source DB is already digitized |
| Original sensor waveform recovery | `vin` is analog-equivalent reconstruction, not true waveform recovery |
| Physical AFE PCB validation | Not performed in this repo |
| ADC silicon measurement | Not performed |
| Virtuoso/post-layout analog verification | Not performed |
| Clinical diagnosis validation | Engineering prototype only |
| Validation 100.00% as final generalization | Validation is model-selection performance |
| Physical analog validation completed by this repo | Evidence is MATLAB/LTspice/XMODEL model-based verification, not bench/silicon measurement |

## Final Result Interpretation

최종 성능 주장은 locked final_test 기준으로만 한다.

| 항목 | 값 |
|---|---:|
| Final test 30-minute chunk | 29 / 36 = 80.56% |
| Final test 30-minute chunk macro F1 / balanced accuracy | 80.44% / 80.56% |
| Final test 30-minute chunk weakest recall | CHF 66.67% |
| Final test record-majority | 16 / 19 = 84.21% |
| Final test record-majority macro F1 / balanced accuracy | 80.80% / 88.19% |
| Final test record-majority weakest recall | CHF 75.00%, ARR 77.78% |

Validation 32/32 = 100.00%는 Final Membrane 후보를 선택하는 단계의 성능이며, 최종 held-out 일반화 성능으로 쓰지 않는다.

## Final Claim-Boundary Statement

This repo is the integrated evidence repository for a model-based MATLAB/LTspice/XMODEL AFE+ADC flow and a signed 12-bit ECG-stream SNN accelerator IP. Analog source development remains upstream, while this repository mirrors the report evidence and provides locked protocol, RTL/XSim, Vivado/IP-XACT, and Vitis/MicroBlaze board replay evidence.

즉 아날로그 원본 개발은 teammate repositories가 소유하지만, 이 repo는 MATLAB 사전설계 -> LTspice schematic 검증 -> SystemVerilog XMODEL 구현의 보고서용 사본과 상관 결과를 보존한다. 디지털 구현은 signed 12-bit stream 이후의 accelerator IP를 소유하며 full-top XSim expected output과 Vitis/MicroBlaze board replay result를 비교한다.
