# Mixed-signal-to-digital 검증

## 역할 분리

MATLAB과 XMODEL은 서로 대체 관계가 아니다. MATLAB은 nominal intent와 reference-vector package를 제공하고, XMODEL은 SystemVerilog 기반 non-ideal/stress와 long-stream handoff를 검증한다. 둘 다 physical AFE/ADC measurement가 아니다.

## MATLAB nominal evidence

고정 commit `907f7e1f...`의 nominal parameter CSV는 HPF 약 0.4823 Hz, IA gain 201, 60 Hz notch, LPF 약 150.15 Hz, ±1.65 V 12-bit ADC를 기록한다. 대표 NSR/CHF/ARR/AFF 60초 record의 clipping ratio는 모두 0%이고 최소 rail headroom은 ARR record에서 약 1.0196 V다. Class별 signed two's-complement reference vector와 SHA256 manifest가 존재한다.

이 값은 nominal digital MATLAB chain의 selected records 결과다. Notch sweep 수치를 physical notch measurement나 전체 population 보증으로 표현하지 않는다.

## XMODEL waveform and stress evidence

고정 commit `4756a508...`의 verification report는 emulator와 Questa/XMODEL 36개 60초 segment를 settling 이후 비교해 평균 RMS 1.95 LSB, lag 0을 기록한다. 최대 국소 편차는 급경사 QRS 구간에서 solver/sub-sample timing 차이에 민감하므로 평균 RMS만으로 bit-exact라고 표현하지 않는다.

Stress scope에는 다음이 포함된다.

- 60 Hz/50 Hz PLI: 설계 target은 60 Hz이며 50 Hz는 retuning 필요
- electrode offset/baseline wander: settling 이후 clipping과 residual 분석
- R/C mismatch: CMRR와 residual 분석; 30분 final_pred는 equivalence-based argument
- finite GBW/VOS: waveform/headroom 영향과 offset caveat
- ADC non-ideal: representative 30분 locked RTL regression; 2 LSB rms noise에서 NSR 한 건 flip

따라서 “모든 non-ideal 조건에서 분류가 불변”이라고 주장하지 않는다.

## Signed-stream handoff

AFE-generated final-test 36 chunks는 digital board-replay `.mem`과 SHA256 36/36 동일하다. Window mapping은 1 kSPS의 1,800,000-sample 30분 chunk를 사용한다. Canonical board-facing XSim cadence `sample_gap_cycles=2`에서 final_pred와 final_mem은 각각 36/36 bit-exact다.

이 검증은 다음 두 단계를 분리해 증명한다.

1. byte-level input identity: AFE chunk와 digital replay input이 동일
2. output-level functional identity: 같은 canonical cadence에서 locked RTL output이 digital golden과 동일

이는 label accuracy 또는 physical analog correctness의 100% 보장이 아니다.
