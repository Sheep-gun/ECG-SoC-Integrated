# ECG AFE·Behavioral ADC LTspice 검증 보강 초안

문장 성격을 `[확인된 사실]`, `[해석]`, `[미완료]`로 표시하였다. 별도 tolerance가 없는 analog metric은 PASS/FAIL이 아니라 `MEASURED`이다.

## 1. LTspice schematic 구성

[확인된 사실] 원본 `FULL_AFE_ADC_SH.asc`는 differential HPF, 3-op-amp IA, active Twin-T 60 Hz notch, 150 Hz LPF/buffer, S/H, behavioral ADC 순으로 연결된다.

[확인된 사실] 원본은 U1~U6의 +5 V rail과 bootstrap divider midpoint에 동일한 `K_DIV` label을 사용하므로, 문서상 0.95 bootstrap이 ideal +5 V source에 clamp되는 연결 오류가 있다.

[확인된 사실] 원본은 수정하지 않고, 최종 validation copy `FULL_AFE_ADC_SH_xmodel_aligned.asc`에서 supply node를 `VPLUS`/`VMINUS`로 분리하고 `K_DIV`를 bootstrap 전용 node로 복구하였다.

[확인된 사실] 최종 copy의 U1~U6 supply는 ±1.65 V이며, 전용 `XOPAMP_XMODEL`은 Aol 100 dB, CMRR 110 dB, Rout 1 ohm, nominal GBW 1 GHz, nominal VOS/noise 0의 계약을 사용한다.

[확인된 사실] nominal input은 `INP_RAW=patient`, `INN_RAW=0 V`이고 patient 값은 50 µs update contract로 적용했다. 이전 floating differential source와 ±5 V/UniversalOpamp2 결과는 `pre_alignment`로 분리하였다.

## 2. nominal AC 검증

[확인된 사실] 별도 AC deck의 excitation은 `INP_RAW=AC 1 V`, `INN_RAW=0 V`이다. 이는 XMODEL 상관용 single-ended differential drive이며 input common-mode는 0.5 V이다.

[확인된 사실] `V(HPF_P,HPF_N)/V(INP_RAW,INN_RAW)`의 -3 dB cutoff는 0.481174 Hz이고 0.4823 Hz target 대비 -0.2335%이다.

[확인된 사실] `V(IA_OUT)/V(HPF_P,HPF_N)`의 10 Hz gain은 200.594 V/V, 46.0463 dB이고 201 V/V target 대비 -0.2021%이다.

[확인된 사실] `V(LPF_IN)/V(IA_OUT)`은 60 Hz에서 -83.557 dB이며 55~65 Hz fine search의 최소점은 59.9995 Hz, -95.435 dB이다.

[확인된 사실] `V(AFE_OUT)/V(LPF_IN)`의 -3 dB cutoff는 150.211 Hz이고 150.15 Hz target 대비 +0.0406%이다.

[해석] 정합 회로는 nominal component/model 수준에서 목표 HPF·IA·notch·LPF 의도를 재현한다. 이 결과는 component tolerance, PCB parasitic 또는 silicon 특성의 검증이 아니다.

## 3. patient ECG transient 검증

[확인된 사실] `patient100_ecg_10s.txt`는 3,600행, 0~9.997222 s, nominal 360 Hz이며 timestamp 중복·역행·NaN·Inf가 없다.

[확인된 사실] graphical ASC를 10.001 s, maxstep 5 µs로 실행하였다. 1~10 s AFE_OUT은 -0.054032~+0.246570 V, 0.300603 Vpp, 0.037796 Vrms이다.

[확인된 사실] settled AFE_OUT의 ±1.65 V ADC range 최소 여유는 1.40343 V이고 continuous clipping은 없다. U1~U6 중 rail에 가장 가까운 U3의 최소 여유는 1.39619 V이다.

[확인된 사실] direct와 S/H 10,000 sample 모두 endpoint clipping count가 0이다. Direct signed-code 범위는 전체 구간 -96~303이다.

[확인된 사실] 5 µs final run과 10 µs companion run의 첫 2,000 sample에서 direct/S&H code difference count는 각각 0이며 AFE_OUT 최대 차이는 22.78 µV이다.

## 4. Track-and-Hold 및 ADC mapping 검증

[확인된 사실] clock은 `PULSE(0 5 900u 1u 1u 98u 1m)`이고 switch의 Vt=2.5 V, Vh=0.1 V를 적용한 turn-off threshold crossing은 첫 period 0.99952 ms 부근이다. Direct aperture는 1.000 ms, S/H valid read는 그 0.1 µs 뒤로 정의했다.

[확인된 사실] acquisition error는 최대 4.445 mV, RMS 50.17 µV, 최대 5.516 LSB이다. Hold edge와 다음 clock rise를 제외한 droop은 최대 22.239 µV, RMS 3.052 µV, 최대 0.02760 LSB이다.

[확인된 사실] 10,000개 hold 중 14개 period가 quantizer boundary를 한 번 통과했으며 한 hold에서 두 번 이상 변한 경우는 없다. 고정 valid phase에서는 period당 한 code를 정의할 수 있다.

[확인된 사실] ADC-only plateau test는 -1.65 V→0/-2048, 0 V→2047/-1, +0.5 LSB 이상→2048/0, +1.65 V→4095/2047을 모두 `MATCH`로 확인했고 out-of-range saturation과 monotonicity도 확인했다.

[확인된 사실] XMODEL-equivalent direct stream과 LTspice S/H stream의 zero-lag MAE는 0.0037 LSB, RMS는 0.0755 LSB, maximum은 5 LSB, correlation은 0.9999984이고 best lag는 0 sample이다. 이는 내부 진단이며 XMODEL equivalence 판정이 아니다.

[해석] ADC는 floor 기반 behavioral quantizer이며 실제 SAR conversion sequence나 transistor 회로가 아니다.

## 5. MATLAB nominal reference 및 XMODEL 상관 상태

[확인된 사실] fixed MATLAB commit `907f7e1f081a9d6a5703a32095d962143315a192`를 MATLAB R2026a에서 실행하였다.

[확인된 사실] XMODEL-aligned LTspice direct와 fixed MATLAB의 1 s 이후 index-aligned 비교는 mean error -0.00111 LSB, MAE 0.678 LSB, RMS 2.225 LSB, maximum 37 LSB, correlation 0.998591, best lag 0 sample이다.

[해석] MATLAB digital IIR notch와 LTspice analog Twin-T는 bit-exact 대상이 아니며 이 값은 nominal intent의 gross consistency 진단이다.

[미완료] Fixed XMODEL source와 상관 TB는 확보했지만 현재 workspace에는 `vsim`, `vlog`, licensed XMODEL runtime이 없다. 따라서 동일 10초 입력의 LTspice↔XMODEL code comparison은 `PENDING_XMODEL_EXECUTION`이며 수치를 추정하지 않았다.

## 6. 비이상성 검증

[확인된 사실] DC offset은 operating point부터 넣지 않고 50 µs에 step으로 인가했다. -200 mV case는 startup 구간 1,024 sample에서 ADC endpoint clipping이 있었지만 2 s 이후 clipping은 0이다. +10 mV case의 fixed-script 20-code recovery diagnostic은 1.586 s였다.

[확인된 사실] ±50~200 mV와 baseline-wander cases 중 +10 mV 이외는 2.000 s search window 끝까지 20-code 차이가 남아 `recovered=false`로 기록했다. 2.000 s를 회복 완료 시간으로 주장하지 않는다.

[확인된 사실] 60 Hz common-mode 0.5 V와 differential 1 mV 주입은 2 s 이후 nominal 대비 RMS code difference 0.0606 LSB, clipping 0이었다. 50 Hz out-of-target diagnostic은 146.61 LSB였다.

[확인된 사실] IA/Twin-T mismatch 0.1/0.5/1%에서 60 Hz attenuation은 각각 -46.001/-31.935/-25.804 dB로 변화했고, PLI60 MM0 대비 settled RMS code difference는 0.901/4.109/8.117 LSB였다.

[확인된 사실] GBW 100 kHz/500 kHz/1 MHz/5 MHz의 nominal 대비 settled RMS code difference는 1.466/0.386/0.237/0.089 LSB였다.

[확인된 사실] U1=+VOS, U2=-VOS의 0.5/1/2 mV case는 settled RMS code difference 248.92/497.83/995.67 LSB였고 clipping은 0이었다.

[확인된 사실] ADC white noise, sample jitter, 30분 regression과 locked `final_pred/final_mem` 영향은 LTspice final stress가 아니라 `XMODEL_OWNED` 또는 `LOCKED_RTL_FPGA_OWNED`로 분류했다.

## 7. 범위와 한계

[확인된 사실] 이 결과는 LTspice 26.0.1 schematic-level model-based verification이다. Physical PCB, fabricated AFE/ADC/SoC, transistor-level SAR, post-layout, live subject 또는 clinical evidence가 아니다.

[확인된 사실] 한 patient의 10초 waveform은 population 전체, 장시간 classification 정확도, XMODEL/RTL equivalence 또는 FPGA 결과를 보증하지 않는다.
