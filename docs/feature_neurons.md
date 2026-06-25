# Feature Neuron 설명

## pNN125

pNN125는 RR hypothesis neuron bank 기반 feature입니다. 다음 QRS가 예측 window 안에 들어오면 match, 벗어나면 mismatch로 판단합니다. window half는 125 ms입니다.

## RDM

RDM은 연속 RR interval 차이의 크기를 spike bank로 표현합니다. pNN125가 예측 window 성공 여부를 본다면, RDM은 실제 RR 변화량을 더 직접적으로 봅니다.

## DSCR

DSCR은 ECG waveform slope sign-change 기반 morphology complexity feature입니다. sign flip과 valid slope event의 비율적 성격을 통해 CHF와 NSR 분리에 주로 기여합니다.

## RAM

RAM은 Random Access Memory가 아니라 R-peak amplitude response feature입니다. beat 주변 R peak amplitude code의 평균 수준을 class evidence로 사용합니다.

## ECP

ECP는 ectopic compensatory pair 성격을 보는 보조 feature입니다. early beat와 compensation 성격을 통해 ARR evidence를 보강합니다.

## QRS MAF

QRS MAF는 QRS width, slope complexity, energy 성격을 통해 morphology abnormality를 감지하는 feature입니다.

## RBBB QRS Delay Bank

RBBB QRS Delay Bank는 RBBB-like conduction delay를 직접 진단하는 임상 모듈이 아니라, single-channel ECG에서 wide QRS와 terminal delay 성격을 proxy로 잡는 feature입니다.

최종 설정은 다음과 같습니다.

- activity mode: abs_delta_ge_low_slope
- width threshold: 110
- terminal threshold: 3
- repeat threshold: 5
- low irregularity: not_high_pnn
- readout: hybrid
- NSR inhibit: 150000
- ARR boost: 150000

## EERG

EERG는 Episodic Ectopic Rescue Gate입니다. RBBB-like beat가 없는 segment 중에서도 pre-QRS bump와 early/ECP evidence가 있는 boundary ARR을 구제하기 위한 readout gate입니다.

조건은 다음과 같습니다.

~~~text
rbbb_like_beat_count == 0
pre_qrs_bump_count >= 1
early_count >= 10 OR ECP_count >= 3
pNN_mismatch_rate <= 0.15
RDM_avg <= 5
~~~

조건을 만족하면 ARR membrane에 25000을 더합니다. AFF inhibition은 사용하지 않습니다.
