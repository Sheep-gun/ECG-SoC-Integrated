# AFE+ADC XMODEL Evidence

## 1. 이 문서의 위치

본 문서는 기존 [AFE+ADC XMODEL 기반 입력 생성 흐름](AFE_ADC_XMODEL_FLOW_KR.md)에 이어, 대회 제출용 figure와 실험 로그를 정리한다. 핵심은 **공개 digitized ECG record를 실제 raw analog ECG로 복원했다고 주장하지 않고**, physical-voltage-equivalent input과 nominal AFE+ADC model evidence를 분리해서 보여주는 것이다.

## 2. 생성한 evidence

실행:

```powershell
python tools\generate_afe_xmodel_evidence.py
```

결과:

- `reports/award_readiness/afe_xmodel_evidence_summary.md`
- `reports/award_readiness/afe_xmodel_evidence_summary.json`
- `reports/award_readiness/figures/afe_vin_reconstruction.png`
- `reports/award_readiness/figures/afe_chain_waveform.png`
- `reports/award_readiness/figures/notch_60hz_effect.png`
- `reports/award_readiness/figures/adc_quantization_hist.png`
- `reports/award_readiness/figures/afe_on_off_comparison.png`
- `reports/award_readiness/figures/afe_frequency_response.png`

## 3. figure 해석

| Figure | 의미 | 주의 |
|---|---|---|
| `afe_vin_reconstruction.png` | signed `.mem` sample을 `vin_v = code / 200000` 기준으로 voltage-equivalent waveform으로 표시 | raw analog recovery가 아님 |
| `afe_chain_waveform.png` | HPF -> gain x201 -> 60 Hz notch -> LPF nominal chain의 waveform | nominal model evidence |
| `notch_60hz_effect.png` | 60 Hz sinusoidal noise injection 후 notch response | 실제 PCB noise measurement 아님 |
| `adc_quantization_hist.png` | 12-bit signed ADC code distribution | 현재 선택 chunk 기준 |
| `afe_on_off_comparison.png` | nominal AFE-on code와 direct quantization 비교 | full dataset accuracy ablation 아님 |
| `afe_frequency_response.png` | HPF/notch/LPF/total nominal response | documented nominal response |

## 4. 검증으로 해석할 수 있는 범위

이 evidence는 다음을 보여준다.

- RTL input이 signed 12-bit `.mem` stream이라는 점
- `code / 200000` scaling으로 voltage-equivalent waveform을 만들 수 있다는 점
- HPF, gain, notch, LPF, ADC quantization stage가 classifier input distribution을 바꾸는 model stage라는 점
- AFE+ADC flow가 단순 file scaling이 아니라 model-in-the-loop 입력 생성 흐름이라는 점

하지만 다음은 주장하지 않는다.

- 실제 AFE PCB 실측
- 실제 ADC silicon measurement
- Virtuoso post-layout simulation
- original raw analog ECG 복원
- PVT/noise/corner 검증 완료

## 5. 향후 보완

- 실제 XMODEL transient output dump를 저장하고 figure에 직접 overlay
- raw/AFE-off, HPF-off, notch-off, LPF-off full-record `.mem` dataset 재생성
- AFE stage별 classifier accuracy ablation
- record별 clipping/saturation report
