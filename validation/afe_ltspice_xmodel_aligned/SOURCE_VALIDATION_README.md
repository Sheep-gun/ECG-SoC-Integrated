# ECG AFE / behavioral ADC LTspice validation package

## Current final candidate

최종 후보는 `schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc`이다.
원본 `../FULL_AFE_ADC_SH.asc`, patient text, DOCX와 model source는 수정하지 않았다.

이 회로는 고정 XMODEL commit `4756a5086023547328ef44fd5fd87da3c250dc39`에 맞춰 다음을 적용했다.

- U1~U6 supply: +1.65 V / -1.65 V
- dedicated op-amp: Aol 100 dB, CMRR 110 dB, Rout 1 ohm, nominal GBW 1 GHz, VOS 0
- nominal drive: ECG+=patient, ECG-=0 V, 50 us input update
- direct ADC aperture: 1.000 ms부터 1 kSPS
- LTspice-only S/H: 각 period 0.900~1.000 ms 부근 track, 1.000 ms 직후 valid hold
- ADC: ±1.65 V limiter, floor(), 0~4095 endpoint mapping, signed=`code-2048`

`UniversalOpamp2`와 ±5 V로 만든 이전 결과는 최종 evidence가 아니다. 해당 표·그림·vector·보고서 초안은 `pre_alignment/`에 보존했다.

## Executed evidence

LTspice 26.0.1에서 XMODEL-aligned graphical nominal, AC/fine-notch, ADC mapping,
timestep convergence, DC/baseline/50·60 Hz/mismatch/GBW/VOS stress 총 35개 run을 실행했다.
모든 run에 raw/log/command record가 있고 fatal 및 warning signature는 0건이다.
목록은 `tables/xmodel_aligned_execution_manifest.csv`에 있다.

Tolerance가 별도로 없으므로 analog 결과는 `MEASURED`로 표시한다.

| Metric | Target | Measured |
|---|---:|---:|
| Differential HPF -3 dB | 0.4823 Hz | 0.481174 Hz (-0.2335%) |
| IA gain at 10 Hz | 201 V/V | 200.594 V/V (-0.2021%) |
| Notch at 60 Hz | — | -83.557 dB |
| Notch minimum | 60 Hz | 59.9995 Hz, -95.435 dB |
| LPF -3 dB | 150.15 Hz | 150.211 Hz (+0.0406%) |
| Settled AFE_OUT | ±1.65 V range | -0.05403~+0.24657 V |
| Settled ADC headroom | — | 1.40343 V |
| Direct/S&H sampled clipping | — | 0 / 10,000 |
| S/H acquisition error | — | max 4.445 mV, RMS 50.17 µV |
| Hold droop | — | max 22.239 µV = 0.02760 LSB |

ADC plateau test는 -1.65 V→0/-2048, 0 V→2047/-1, +0.5 LSB 이상→2048/0,
+1.65 V→4095/2047, out-of-range saturation과 monotonicity를 모두 `MATCH`로 확인했다.

## Streams

- `results/xmodel_aligned/nominal/ltspice_xmodel_aligned_adc_samples.csv`: direct와 S/H를 한 행에서 비교
- `results/xmodel_aligned/nominal/ltspice_xmodel_aligned_direct_adc_signed.mem`: XMODEL-aligned LTspice direct aperture stream
- `results/xmodel_aligned/nominal/ltspice_track_hold_adc_signed.mem`: LTspice S/H stream

두 `.mem`은 LTspice-derived vector이며 official locked XMODEL/RTL vector가 아니다.

## Cross-model status

- Fixed MATLAB commit `907f7e1f081a9d6a5703a32095d962143315a192`: MATLAB R2026a에서 실행됨. Settled index-aligned MAE 0.678 LSB, RMS 2.225 LSB, correlation 0.998591. MATLAB digital notch와 LTspice analog notch는 bit-exact 대상이 아니다.
- Fixed XMODEL source와 stress contract는 commit `4756a5086023547328ef44fd5fd87da3c250dc39` 기준으로 보존했다. 이 LTspice source snapshot 작성 당시 직접 실행은 `PENDING_XMODEL_EXECUTION`이었으나, 후속 team handoff에서 동일 10초 ECG 10,000-sample 직접 비교를 완료했다. Full-range 결과는 MAE 0.6445 LSB, RMS 1.3020 LSB, maximum 13 LSB, correlation 0.999518, lag 0, clipping 0이며 98.74%가 ±5 LSB, 99.89%가 ±10 LSB 이내다. 최신 통합 서술과 figure는 `../../reports/final/analog_validation_result.md`를 따른다.

## Directory guide

- `audit/`: 원본 회로 감사, XMODEL alignment audit, node/component crosswalk
- `schematics/xmodel_aligned/`: 최종 graphical ASC, generated netlist, model/symbol, 모든 deck
- `results/xmodel_aligned/`: 최종 raw/log/vector/export
- `tables/xmodel_aligned_*`: 최종 정량 표와 execution QC
- `plots/xmodel_aligned_*`: 최종 scripted SVG
- `reference/`: fixed MATLAB/XMODEL source와 provenance
- `pre_alignment/`: ±5 V/UniversalOpamp2 과거 증거
- `report/`: 보고서 보강 초안, caption, 한계, stress 해석, handoff

## Re-run

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

기존 raw만 다시 parse할 때는 `-ParseOnly`; MATLAB을 생략하려면 `-SkipMatlab`을 사용한다.
전체 ASCII raw는 약 13.9 GB이므로 충분한 disk 공간이 필요하다.

## Scope boundary

이 package는 LTspice schematic-level model-based verification과 behavioral quantizer evidence다.
Physical SAR ADC, PCB/bench, fabricated IC/SoC, transistor/post-layout, live subject/clinical,
XMODEL/RTL equivalence 또는 4-class accuracy 증거가 아니다.
