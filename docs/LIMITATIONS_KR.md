# Limitations

## Claim Boundary

| Claim | Status |
|---|---|
| SNN-inspired ECG Classification Accelerator IP Core | supported |
| AFE+ADC XMODEL-linked input generation | supported |
| fully blind strict record-wise locked final holdout | supported |
| Vivado/IP-XACT packaged accelerator IP | supported |
| Vitis/MicroBlaze class-wise board replay | supported |
| direct electrode ECG acquisition | not performed |
| physical AFE board measurement | not performed |
| ADC silicon measurement | not performed |
| transistor-level layout verification | not performed |
| medical diagnosis validation | not performed |

## 해석상 주의

공개 ECG dataset은 already digitized record이다. 따라서 본 프로젝트의 `vin` reconstruction은 analog-equivalent/PWL-equivalent input generation이지 원래 analog waveform 복원이 아니다.

Validation 100%는 model selection 단계의 성능이다. 최종 일반화 성능은 locked final_test chunk 29/36 = 80.56%와 record-majority 16/19 = 84.21%로 보고한다.

Board replay는 NSR/CHF/ARR/AFF 대표 4개 30분 record에서 수행했다. 전체 final_test 36개 case board batch와 board current/power measurement는 수행하지 않았다.

## 금지 표현

- original sensor waveform recovered
- actual AFE board verified
- ADC silicon measured
- transistor-level layout verified
- medical diagnosis validated
- validation accuracy as final generalization
