# Figure 후보 및 caption

## Figure 1. XMODEL-aligned LTspice nominal AFE 및 behavioral ADC schematic

±1.65 V 전원, Aol 100 dB·CMRR 110 dB·Rout 1 Ω의 전용 op-amp abstraction, ECG+=patient/ECG-=0 입력, differential HPF, 3-op-amp IA, active Twin-T, 150 Hz LPF/buffer, LTspice Track-and-Hold와 floor 기반 12-bit behavioral ADC를 보인다. Schematic-level model-based 구성이고 physical SAR ADC, PCB, transistor/post-layout 결과가 아니다.

## Figure 2. HPF·IA·Twin-T·LPF nominal AC response

독립 AC deck으로 계산한 XMODEL-aligned stage transfer를 나타낸다. HPF -3 dB는 0.481174 Hz, IA 10 Hz gain은 200.594 V/V, Twin-T는 60 Hz에서 -83.557 dB, LPF -3 dB는 150.211 Hz였다. 수치는 model-based LTspice 결과이며 실제 부품·PCB 측정이 아니다.

## Figure 3. Patient ECG stage-by-stage transient

Patient #100 10초 입력에 대한 input, IA, analog Twin-T output과 AFE_OUT을 표시한다. 1초 전후를 분리해 초기 HPF 상태를 steady-state로 오해하지 않도록 했다. 한 patient 예시는 population/clinical 성능이나 4-class accuracy를 보증하지 않는다.

## Figure 4. 1 kSPS Track-and-Hold 및 ADC code 갱신 확대

QRS-like 최대 slope 부근에서 AFE_OUT, CLK, ADC_HOLD, ADC_CODE, ADC_SIGNED와 1 ms aperture를 표시한다. ADC는 behavioral quantizer이고 실제 SAR 회로가 아니다. S/H는 LTspice 추가 구현이며 fixed XMODEL direct sample과 분리해 해석한다.

## Figure 5. MATLAB–LTspice nominal output 비교

Fixed MATLAB digital-filter output과 XMODEL-aligned LTspice analog Twin-T direct code를 index-aligned 및 best-lag diagnostic으로 비교한다. MATLAB digital notch와 LTspice analog notch는 bit-exact 대상이 아니다. 이 그림은 XMODEL/RTL equivalence 증거가 아니다.

## Figure 6. 정의된 analog non-ideal stress 결과

Fixed XMODEL에서 확인한 DC offset/baseline, 50·60 Hz interference, IA/Twin-T mismatch, GBW와 U1/U2 VOS를 ±1.65 V LTspice schematic에서 평가한 code difference를 요약한다. ADC noise/jitter와 장시간/locked RTL 영향은 XMODEL/RTL 소유 범위다. Physical PCB, fabricated IC, transistor/post-layout 또는 clinical stress 결과가 아니다.

## Figure 7. LTspice–fixed XMODEL correlation gate

동일 10초 입력, ECG+=patient/ECG-=0, 첫 1 ms falling-edge aperture에서 LTspice S/H signed code와 fixed XMODEL output을 비교하였다. 10,000 sample 기준 MAE 0.6445 LSB, correlation 0.999518, lag 0, clipping 0이며 98.74%가 ±5 LSB, 99.89%가 ±10 LSB 이내다. 결과 plot은 `../../../figures/final/SPICE-05_xmodel_ltspice_adc_waveform_full.png`부터 `SPICE-10_xmodel_ltspice_adc_metrics.png`까지 보존한다.
