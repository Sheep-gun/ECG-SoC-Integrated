# XMODEL-aligned LTspice stress 해석

Stress 값과 적용 범위는 fixed XMODEL commit `4756a5086023547328ef44fd5fd87da3c250dc39`에서 가져왔다. 모든 수치는 `tables/xmodel_aligned_stress_results.csv`의 LTspice schematic/model 결과이며 tolerance가 없어 `MEASURED`이다.

## LTspice 담당

- 50 µs step DC offset 및 startup recovery
- 0.1 Hz/1 mV, 0.2 Hz/2 mV baseline wander
- common-mode 0.5 V + differential 1 mV의 60 Hz/50 Hz interference
- IA/Twin-T 0/0.1/0.5/1% deterministic mismatch
- U1~U6 finite GBW 100 kHz/500 kHz/1 MHz/5 MHz
- U1/U2 differential VOS 0.5/1/2 mV
- ±1.65 V saturation/headroom 및 LTspice Track-and-Hold

## 핵심 관찰

- -200 mV step은 startup clipping 1,024 sample을 만들었으나 2 s 이후 clipping은 없었다.
- +10 mV는 20-code diagnostic 기준 1.586 s에서 마지막 초과가 관측됐다. 더 큰 DC와 baseline cases의 2.000 s 값은 search-window censoring이며 recovery 완료가 아니다.
- 60 Hz notch target에서는 PLI residual이 0.0606 LSB RMS였고 50 Hz diagnostic은 146.61 LSB RMS였다.
- mismatch 증가에 따라 notch depth와 common-mode rejection이 악화됐다. 1%에서 60 Hz attenuation은 -25.804 dB였다.
- finite GBW 영향은 100 kHz가 가장 컸고 5 MHz에서 nominal에 가까워졌다.
- VOS는 201 V/V IA 구조에서 크게 증폭됐다. 2 mV case의 settled RMS code difference는 995.67 LSB였지만 이 5 s run의 endpoint clipping은 0이었다.

## XMODEL/RTL 담당

ADC white noise, sample jitter, 30분 locked regression, `final_pred/final_mem`과 classification 영향은 `XMODEL_OWNED` 또는 `LOCKED_RTL_FPGA_OWNED`이다. LTspice에서 중복 삽입하지 않았으며 PENDING으로 오표기하지 않는다.

이 결과는 정의된 deterministic stress의 schematic-level 모델 응답이며 실제 부품 tolerance distribution, Monte Carlo silicon yield 또는 의료환경 내성을 뜻하지 않는다.
