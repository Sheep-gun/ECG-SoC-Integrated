# Analog AFE+ADC Verification: MATLAB -> LTspice -> XMODEL

## 1. 검증 목적과 역할 분리

본 아날로그 검증은 하나의 simulator 결과를 반복 제시하는 것이 아니라, 같은 AFE+ADC를 세 단계에서 서로 다른 목적으로 확인한다.

| 단계 | 핵심 질문 | 검증 산출물 |
|---|---|---|
| MATLAB 사전설계 | 목표 HPF/IA/notch/LPF/ADC 응답이 수학적으로 적절한가? | nominal transfer function, cutoff/gain/notch reference, ADC reference vector |
| LTspice 실제 구현·검증 | 목표 사양을 실제 R/C, op-amp, 전원, S/H와 ADC mapping으로 구현했을 때 동일한 응답을 얻는가? | graphical `.asc`, generated `.net`, AC/transient/S&H/ADC/stress 결과 |
| SystemVerilog XMODEL | LTspice로 고정한 회로 계약을 RTL과 함께 실행할 수 있는 mixed-signal 행동모델로 재현하는가? | XMODEL primitive 기반 `.sv`, stress variants, 1 kSPS signed 12-bit stream |

따라서 검증 흐름은 다음 한 줄로 고정한다.

> **MATLAB design reference -> LTspice schematic evidence -> SystemVerilog XMODEL implementation -> signed 12-bit RTL handoff**

![Figure A-1. ECG AFE+ADC architecture and non-ideality injection points](figures/analog_validation/01_analog_afe_architecture.svg)

신호 경로는 differential HPF, 3-op-amp instrumentation amplifier, 60 Hz active Twin-T notch, 150 Hz LPF와 buffer, 12-bit ADC 순서다. R/C mismatch, op-amp GBW/VOS와 ADC non-ideality는 nominal path와 분리하여 주입한다.

## 2. MATLAB 사전설계

MATLAB 단계는 실제 부품의 전기적 구현을 주장하지 않는다. HPF cutoff, IA gain, 60 Hz 제거, LPF bandwidth와 ADC 범위를 빠르게 탐색하고 이후 LTspice와 XMODEL이 따라야 할 nominal reference를 고정한다.

| 설계 항목 | MATLAB/LTspice 공통 기준 |
|---|---:|
| Differential HPF | 약 0.482 Hz |
| Instrumentation amplifier | 약 201 V/V |
| Power-line rejection | 60 Hz active Twin-T notch |
| Anti-alias LPF | 약 150 Hz |
| ADC | 12-bit, ±1.65 V, 1 kSPS |

![Figure A-2. MATLAB reference and LTspice full AFE frequency-response comparison](figures/analog_validation/03_matlab_ltspice_afe_response.png)

전체 응답에서 MATLAB과 LTspice는 약 46 dB의 passband gain, 저주파 HPF roll-off, 60 Hz notch와 150 Hz 이후 LPF roll-off를 동일하게 재현한다. 60 Hz 구간은 별도의 dense sweep으로 확인했다.

![Figure A-3. MATLAB reference and LTspice active Twin-T notch comparison](figures/analog_validation/04_matlab_ltspice_notch_response.png)

고정 MATLAB reference와 XMODEL-aligned LTspice의 1초 이후 index-aligned ADC 비교는 MAE 0.678 LSB, RMS 2.225 LSB, correlation 0.998591이었다. MATLAB의 digital-filter reference와 LTspice의 analog Twin-T는 구현 방식이 다르므로 bit-exact 대상이 아니라 설계 의도와 파형의 gross consistency 확인에 사용한다.

## 3. LTspice schematic 구현과 회로 수준 검증

MATLAB에서 고정한 사양을 [`FULL_AFE_ADC_SH_xmodel_aligned.asc`](../../validation/afe_ltspice_xmodel_aligned/schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc)로 구현했다. 최종 회로는 기존 ±5 V 후보와 분리하며, XMODEL contract에 맞춘 ±1.65 V 전원, 100 dB open-loop gain, 110 dB CMRR, 1 Ω output resistance, nominal 1 GHz GBW의 전용 op-amp abstraction을 사용한다. 입력은 `ECG+=patient100`, `ECG-=0 V`, 50 µs update이며 첫 ADC aperture는 1.000 ms, 이후 1 kSPS다.

![Figure A-4. XMODEL-aligned LTspice AFE+ADC/S&H schematic](figures/analog_validation/02_ltspice_xmodel_aligned_schematic.jpg)

### 3.1 Nominal AC와 transient 결과

| 항목 | 목표 | LTspice 측정 | 해석 |
|---|---:|---:|---|
| HPF -3 dB | 0.4823 Hz | 0.481174 Hz | -0.2335% |
| IA gain at 10 Hz | 201 V/V | 200.594 V/V | -0.2021% |
| Notch at 60 Hz | 60 Hz rejection | -83.557 dB | power-line band 제거 |
| Notch minimum | 60 Hz | 59.9995 Hz, -95.435 dB | 중심주파수 정합 |
| LPF -3 dB | 150.15 Hz | 150.211 Hz | +0.0406% |
| Settled AFE output | ±1.65 V 이내 | -0.0540~+0.2466 V | clipping 없음 |
| ADC rail headroom | clipping 없음 | 1.403 V | 충분한 nominal headroom |
| S/H hold droop | 최소화 | 최대 0.0276 LSB | ADC code 영향이 매우 작음 |

LTspice 26.0.1에서 nominal graphical run, AC/fine-notch, ADC mapping, timestep convergence, DC/baseline, 50/60 Hz PLI, R/C mismatch, GBW와 VOS를 포함한 35개 run을 실행했다. 모든 run은 `EXECUTED`이고 fatal/warning signature는 0건이다. 세부 결과는 [`xmodel_aligned_execution_manifest.csv`](../../validation/afe_ltspice_xmodel_aligned/tables/xmodel_aligned_execution_manifest.csv)와 [`xmodel_aligned_stress_results.csv`](../../validation/afe_ltspice_xmodel_aligned/tables/xmodel_aligned_stress_results.csv)에 보존한다.

### 3.2 ADC mapping과 sample-and-hold

ADC는 ±1.65 V를 0~4095로 제한·양자화한 뒤 signed code `code-2048`로 전달한다. -1.65 V, 0 V, +0.5 LSB, +1.65 V와 범위 밖 입력에서 endpoint saturation, signed mapping과 monotonicity를 확인했다. 10초 ECG nominal run은 direct aperture와 LTspice S/H stream 모두 10,000 sample을 생성했고 clipping은 0건이었다.

## 4. SystemVerilog XMODEL 구현

LTspice에서 확인한 토폴로지와 파라미터는 XMODEL solver primitive 기반 SystemVerilog로 작성했다.

- [`ecg_afe_xmodel.sv`](../../validation/afe_ltspice_xmodel_aligned/reference/xmodel_fixed_4756a50_subset/analog/ecg_afe_xmodel.sv): nominal HPF/IA/active Twin-T/LPF/buffer/ADC chain
- [`ecg_afe_xmodel_op.sv`](../../validation/afe_ltspice_xmodel_aligned/reference/xmodel_fixed_4756a50_subset/analog/ecg_afe_xmodel_op.sv): finite GBW와 input offset variant
- [`ecg_afe_xmodel_mm.sv`](../../validation/afe_ltspice_xmodel_aligned/reference/xmodel_fixed_4756a50_subset/analog/ecg_afe_xmodel_mm.sv): R/C mismatch variant

`xreal`, `resistor`, `capacitor`, `vcvs`, `vlimit` primitive로 회로망을 구성하고 `negedge clk_samp`에서 12-bit ADC를 갱신한다. 이 모델은 LTspice를 대체하는 물리 측정 모델이 아니라, 회로 수준에서 확인된 동작을 mixed-signal/RTL simulation으로 전달하는 executable behavioral implementation이다.

## 5. LTspice-XMODEL 10초 ADC 상관 검증

동일한 `patient100` ECG 10초 입력, ±1.65 V ADC 범위, 1 kSPS sampling과 signed 12-bit mapping으로 10,000개 code를 비교했다. 공식 비교에는 LTspice sample-and-hold output을 사용한다.

![Figure A-5. Full-range XMODEL-LTspice ADC waveform overlay](figures/analog_validation/05_xmodel_ltspice_adc_waveform_full.png)

![Figure A-6. XMODEL-LTspice ADC waveform zoom at 2-3 s](figures/analog_validation/06_xmodel_ltspice_adc_waveform_zoom.png)

두 파형은 zero-lag에서 중첩되며, 잔여 차이는 급격한 QRS edge의 sub-sample solver timing 부근에 집중된다.

![Figure A-7. Per-sample LTspice S/H minus XMODEL ADC error](figures/analog_validation/07_xmodel_ltspice_adc_error.png)

### 5.1 정량 결과

![Figure A-8. Quantitative XMODEL-LTspice ADC comparison](figures/analog_validation/10_xmodel_ltspice_adc_metrics.png)

| Metric | Full 10 s result | Settled 1-10 s result |
|---|---:|---:|
| Compared samples | 10,000 | 9,001 |
| XMODEL signed min / max | -96 / 302 | -68 / 302 |
| LTspice signed min / max | -96 / 303 | -68 / 303 |
| Mean error | +0.0221 LSB | +0.0270 LSB |
| MAE | 0.6445 LSB | 0.6549 LSB |
| RMS error | 1.3020 LSB | 1.3243 LSB |
| Maximum absolute error | 13 LSB | 13 LSB |
| Zero-lag correlation | 0.999518 | 0.999502 |
| Best lag | 0 sample | 0 sample |
| Bit-exact ratio | 56.49% | 56.23% |
| Clipping | 0 | 0 |

12-bit ±1.65 V ADC에서 1 LSB는 약 0.806 mV다. 따라서 5 LSB와 10 LSB는 각각 ADC 입력 기준 약 4.03 mV와 8.06 mV이며, IA gain 201을 역산하면 ECG 입력 기준 약 20 µV와 40 µV에 해당한다.

### 5.2 보고서 판정 기준

서로 다른 analog solver의 출력은 bit-exact 여부보다 code-error coverage로 평가한다. 본 보고서에서는 ±5 LSB를 nominal agreement band, ±10 LSB를 extended QRS-edge band로 사용한다.

![Figure A-9. Cumulative ADC-code agreement by error range](figures/analog_validation/09_xmodel_ltspice_adc_agreement.png)

| Error band | Samples inside band | Coverage |
|---|---:|---:|
| 0 LSB, exact | 5,649 | 56.49% |
| ±1 LSB | 9,119 | 91.19% |
| ±2 LSB | 9,556 | 95.56% |
| ±3 LSB | 9,720 | 97.20% |
| ±5 LSB | 9,874 | 98.74% |
| ±10 LSB | 9,989 | 99.89% |

10,000개 중 11개만 ±10 LSB를 초과했고 최대 오차는 13 LSB였다. 평균 절대 오차가 1 LSB보다 작고, lag 0, correlation 0.999518, clipping 0이므로 XMODEL은 LTspice의 nominal AFE+ADC 동작을 RTL integration에 사용할 수 있는 수준으로 재현한다. 다만 이 결과를 bit-exact라고 표현하지 않으며, 급격한 QRS edge의 solver/input-grid timing residual을 함께 명시한다.

![Figure A-10. ADC error histogram](figures/analog_validation/08_xmodel_ltspice_adc_error_histogram.png)

## 6. Digital handoff와 보고서 결론

XMODEL ADC 출력은 signed 12-bit, 1 kSPS stream으로 디지털 accelerator에 전달된다. MATLAB은 사전설계, LTspice는 실제 schematic 검증, XMODEL은 SystemVerilog mixed-signal 실행과 RTL handoff를 담당하므로 각 결과를 하나의 동일성 주장으로 섞지 않는다.

보고서용 결론은 다음과 같다.

> MATLAB에서 고정한 AFE+ADC 사양을 LTspice의 ±1.65 V 실제 schematic으로 구현하여 nominal, sample-and-hold, ADC mapping과 비이상 조건을 검증하였다. 검증된 회로 계약을 SystemVerilog XMODEL로 구현하고 동일한 10초 ECG 10,000 sample을 비교한 결과, 98.74%가 ±5 LSB, 99.89%가 ±10 LSB 이내였으며 MAE 0.6445 LSB, zero-lag correlation 0.999518, clipping 0을 얻었다. 따라서 XMODEL은 LTspice 회로 동작을 높은 정합도로 재현하며 signed 12-bit digital accelerator 입력 생성에 사용된다.

## 7. 범위와 한계

- Source ECG는 실제 전극에서 이번 설계가 직접 계측한 신호가 아니라 공개 digitized record다.
- LTspice와 XMODEL은 schematic/behavioral model-based verification이며 physical PCB, ADC silicon, transistor-level 또는 post-layout 측정이 아니다.
- MATLAB digital reference와 analog Twin-T, LTspice solver와 XMODEL solver 사이의 결과를 bit-exact라고 주장하지 않는다.
- 10초 `patient100` 상관은 대표 nominal case다. 장시간 분류 성능은 별도의 locked RTL/XSim/Vivado/board evidence로 평가한다.

그림 원본명, 저장소 파일명과 SHA-256은 [`figures/analog_validation/FIGURE_INDEX.md`](figures/analog_validation/FIGURE_INDEX.md)에 기록한다.
