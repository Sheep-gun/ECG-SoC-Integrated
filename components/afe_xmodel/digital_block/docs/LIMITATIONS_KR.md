# Limitations and Claim Boundary

## Claim Boundary

| 주장 가능 | 근거 |
|---|---|
| SNN-inspired ECG Classification Accelerator IP Core | RTL, AXI wrapper, IP-XACT package |
| AFE+ADC XMODEL-linked input generation | analog-equivalent `vin` reconstruction, XMODEL output stream |
| Fully blind strict record-wise locked final holdout | final_test not used for selection/search/context, evaluation count 1 |
| Python/XSim bit-accurate locked final-layer check | final_pred/final_mem mismatch 0 over 36 final_test cases |
| Vivado implementation evidence | timing/resource/power reports |
| Vitis/MicroBlaze 36-case board replay | UART transcripts and expected-vs-board CSV for 36 strict final_test 30-minute cases |

## 주장 금지

| 주장 금지 | 이유 |
|---|---|
| Raw analog ECG acquisition | Source DB is already digitized |
| Original sensor waveform recovery | `vin` is analog-equivalent reconstruction, not true waveform recovery |
| Physical AFE PCB validation | Not performed |
| ADC silicon measurement | Not performed |
| Virtuoso/post-layout analog verification | Not performed |
| Clinical diagnosis validation | Engineering prototype only |
| Validation 100.00% as final generalization | Validation is model-selection performance |
| Physical analog board validation | Board replay is digital RTL/IP integration evidence, not DAC/electrode/AFE PCB validation |

## Final Result Interpretation

최종 성능 주장은 locked final_test 기준으로만 한다.

| 항목 | 값 |
|---|---:|
| Final test 30분 chunk | 29 / 36 = 80.56% |
| Final test 30분 chunk macro F1 / balanced accuracy | 80.44% / 80.56% |
| Final test 30분 chunk weakest recall | CHF 66.67% |
| Final test record-majority | 16 / 19 = 84.21% |
| Final test record-majority macro F1 / balanced accuracy | 80.80% / 88.19% |
| Final test record-majority weakest recall | CHF 75.00%, ARR 77.78% |

Validation 32/32 = 100.00%는 Final Membrane 후보를 선택하는 단계의 성능이며, 최종 held-out 일반화 성능으로 쓰지 않는다.

## 심사 대응 핵심 문장

본 프로젝트는 실제 전극 기반 의료기기 검증이 아니라, AFE+ADC XMODEL과 SNN-inspired RTL Accelerator IP Core를 연결한 biomedical mixed-signal-to-digital FPGA prototype이다. 공개 digitized ECG record를 analog-equivalent `vin`으로 재구성하고, AFE+ADC XMODEL을 통과시켜 생성한 signed 12-bit stream을 RTL/IP에 입력하여 장시간 ECG 4-class classification을 수행한다.
