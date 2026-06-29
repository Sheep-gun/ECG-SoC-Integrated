# SNN ECG 4-Class Classifier 최종 마무리 보고서

## 0. 요약

본 프로젝트는 AFE+ADC를 거친 ECG stream을 저전력 RTL 회로에서 처리하여
NSR / CHF / ARR / AFF 4개 class를 분류하는 SNN-inspired ECG classifier를
구현하고 검증하는 것을 목표로 한다.

최종 시스템은 하나의 긴 ECG record를 한 번에 분류하지 않는다. Holter ECG처럼
긴 시간 동안 ECG를 관찰한다는 관점에서, 입력 ECG stream을 고정 길이 구간으로
반복 평가하고, 각 구간에서 발생한 class evidence를 membrane에 누적해 최종
class를 결정한다.

최종 구조는 다음과 같다.

```text
full-record ECG
-> AFE+ADC signed 12-bit stream
-> 60초 Snapshot C24 classifier
-> 30분 chunk-level snapshot vote membrane
-> record-level Final Membrane Layer
-> NSR / CHF / ARR / AFF 최종 판정
```

현재 최종 검증 결과는 다음과 같다.

| 항목 | 결과 |
| --- | ---: |
| 60초 Snapshot C24 test accuracy | 193 / 240 = 80.42% |
| 30분 final membrane Python test accuracy | 30 / 36 = 83.33% |
| 30분 final membrane XSim test accuracy | 30 / 36 = 83.33% |
| Python-vs-XSim prediction mismatch | 0 / 136 |
| full RTL top resource | 20,256 LUT / 2,259 FF / DSP 0 / BRAM 0 |
| final membrane chain resource | 163 LUT / 157 FF / DSP 0 / BRAM 0 |

정량 전력 소모량은 아직 최종 산출하지 않았다. 현재 저장소에 남은 전력 관련
근거는 synthesis resource 결과이며, mW 단위 전력은 Vivado implementation,
clock constraint, switching activity(SAIF/VCD) 기반 `report_power`를 추가로
수행해야 한다.

## 1. 연구 목적

일반적인 12-lead ECG는 짧은 시간의 심전도만 기록한다. 그러나 부정맥은
간헐적으로 나타나는 경우가 많고, 짧은 ECG만으로는 환자의 rhythm abnormality를
포착하지 못할 수 있다. Ambulatory ECG 또는 Holter monitor는 이러한 문제를
해결하기 위해 24-48시간 동안 ECG를 지속적으로 기록하고, 그 안에서 특정 rhythm
abnormality 또는 arrhythmia pattern을 찾는 방식이다.

본 연구의 목적은 이러한 Holter-style monitoring 흐름을 FPGA/RTL 관점에서
저전력 SNN-inspired 구조로 옮기는 것이다. 즉, ECG를 한 번에 큰 벡터로 변환해
software classifier에 넣는 것이 아니라, ECG stream에서 event spike를 만들고,
그 event들이 class neuron membrane에 누적되도록 설계한다.

최종 목표는 다음과 같다.

1. AFE+ADC 이후의 signed 12-bit ECG stream을 직접 입력으로 받는다.
2. 60초 단위 Snapshot C24 classifier가 NSR / CHF / ARR / AFF evidence를 만든다.
3. 여러 snapshot의 발화 패턴을 Final Membrane Layer가 누적한다.
4. record 또는 30분 chunk 단위에서 최종 class를 WTA로 결정한다.
5. 모든 핵심 연산은 counter, comparator, signed accumulator, threshold, WTA로 구현한다.
6. floating point, divider, DSP multiplier, backpropagation, STDP는 사용하지 않는다.

## 2. Holter 방식에서 받은 설계 동기

Holter monitor는 보통 24-48시간 동안 ECG를 연속 기록하며, QRS complex와 R-R
interval을 주요 분석 대상으로 삼는다. 또한 ambulatory ECG는 표준 ECG에서
쉽게 잡히지 않는 intermittent arrhythmia 또는 arrhythmia pattern을 찾기 위해
사용된다.

이 프로젝트의 핵심 설계 방향도 같다.

```text
짧은 ECG 하나로 환자를 확정 진단
X

긴 ECG stream에서 반복적으로 나타나는 snapshot evidence를 누적
O
```

다만 실제 데이터셋 구성 과정에서 ARR class의 원천 데이터인 MIT-BIH Arrhythmia
Database는 30분 excerpt 중심으로 구성되어 있었다. 반면 NSR, CHF, AFF는 더 긴
record를 제공한다. 따라서 모든 class를 24시간 기준으로 맞추면 ARR class가
데이터 길이 측면에서 불리하고, class별 record duration imbalance가 매우 커진다.

그래서 최종 실험에서는 24시간 전체 record classification 대신, annotation-valid
30분 chunk를 class-balanced하게 구성했다.

이 선택의 의미는 다음과 같다.

1. 본래 지향점은 24-48시간 Holter-style monitoring이다.
2. 공개 데이터셋의 ARR 길이 한계 때문에 최종 정량 검증은 30분 chunk 기준으로 제한했다.
3. 구조 자체는 30분에 종속되지 않는다. Timer neuron과 record-level membrane을 확장하면 24시간 stream으로 확장 가능하다.
4. 30분 chunk 검증은 “장시간 stream을 60초 snapshot으로 반복 평가하고 누적한다”는 계층형 구조의 축소 실험이다.

## 3. 사용 데이터셋

최종 30분 dataset은 PhysioNet 계열 ECG database에서 가져온 full-record AFE+ADC
stream을 기반으로 만들었다.

| Class | Source DB | 목적 |
| --- | --- | --- |
| NSR | MIT-BIH Normal Sinus Rhythm Database (`nsrdb`) | 정상 동리듬 record |
| CHF | BIDMC Congestive Heart Failure Database (`chfdb`) | severe CHF subject ECG |
| ARR | MIT-BIH Arrhythmia Database (`mitdb`) | arrhythmia excerpt |
| AFF | MIT-BIH Atrial Fibrillation Database (`afdb`) | AF/AFL rhythm 포함 record |

최종 데이터셋 경로:

```text
fullrec_afe_30min_annotation_valid_balanced/
```

최종 manifest:

```text
fullrec_afe_30min_annotation_valid_balanced/annotation_valid_balanced_30min_manifest.csv
```

최종 split/class 분포:

| Split | NSR | CHF | ARR | AFF | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 17 | 17 | 17 | 17 | 68 |
| val | 8 | 8 | 8 | 8 | 32 |
| test | 9 | 9 | 9 | 9 | 36 |
| all | 34 | 34 | 34 | 34 | 136 |

record 기준 분포:

| Class | Records | 30분 chunks |
| --- | ---: | ---: |
| NSR | 18 | 34 |
| CHF | 14 | 34 |
| ARR | 34 | 34 |
| AFF | 4 | 34 |
| ALL | 70 | 136 |

주의할 점:

1. ARR은 MIT-BIH Arrhythmia Database의 30분 excerpt 성격 때문에 chunk 수가 구조적으로 제한된다.
2. AFF는 4개 record에서 여러 30분 chunk를 뽑았으므로 record 다양성은 제한적이다.
3. CHF label은 record-level CHF label이다. beat annotation만으로 “CHF rhythm”을 직접 증명하는 것은 아니므로, annotation-valid 조건은 AFIB/AFL contamination 등을 제거하는 clean-enough CHF chunk 선별로 해석한다.
4. 최종 split은 record-wise leakage를 피하도록 audit했다.

## 4. AFE+ADC 변환

최종 digital core 입력은 raw ECG가 아니라 AFE+ADC를 거친 signed 12-bit stream이다.
따라서 Snapshot C24와 Final Membrane 검증은 모두 `.mem` 형태의 signed ADC code를
기준으로 수행했다.

변환 흐름:

```text
WFDB ECG channel
-> linear resampling to 1 kSPS
-> AFE-equivalent filtering/gain
-> ADC quantization
-> signed 12-bit readmemh-compatible .mem
-> RTL adc_data input
```

AFE/ADC 조건:

| 항목 | 값 |
| --- | --- |
| sample rate | 1 kSPS |
| input scaling | `V = code / 200000` |
| HPF cutoff | 0.482 Hz |
| instrumentation amplifier gain | x201 |
| notch | 60 Hz Twin-T notch, Q 약 5 |
| LPF cutoff | 150 Hz |
| ADC reference | +/- 1.65 V |
| ADC full span | 3.3 V |
| ADC resolution | 12-bit |
| intermediate format | offset-binary unsigned |
| RTL input format | signed = unsigned - 2048 |

각 record의 앞부분 2초는 AFE/HPF settling 구간으로 보고 skip했다. 30분 dataset에서는
settling skip 이후 1,800,000 sample 단위로 non-overlapping chunk를 만들고, 마지막
30분 미만 tail은 버렸다.

## 5. 전체 모델 구조

최종 모델은 두 계층으로 구성된다.

```text
Layer 1: Snapshot C24
  - 60초 ECG 구간 하나를 4-class로 분류
  - ECG event spike와 feature evidence를 class membrane에 누적
  - 60초 끝에서 WTA로 snapshot pred_class 출력

Layer 2: Final Membrane Layer
  - 30분 chunk 안의 60초 snapshot 30개를 누적
  - 같은 record의 chunk들을 다시 record-level membrane에 누적
  - record_done 시점에 WTA로 최종 class 출력
```

RTL top:

```text
rtl/snn_ecg_30min_final_top.v
```

핵심 RTL 파일:

```text
rtl/core/snn_ecg_3feat_top.v
rtl/core/class_score_neurons.v
rtl/final_membrane_layer.v
rtl/record_level_final_membrane_layer.v
sim/tb_snn_ecg_30min_record_level_dataset.v
```

## 6. Timer Neuron 기반 60초 Snapshot Boundary

초기에는 60,000 sample counter로 snapshot을 끊는 구조였다. 그러나 단순 sample
counter는 SNN-style 구조와 맞지 않는다는 판단에 따라 timer-neuron 형태로
리팩터링했다.

현재 구조:

```text
sample_valid spike
-> timer_mem += 1
-> timer_mem == 60000 - 1
-> snapshot_boundary_spike 발생
-> Snapshot C24 segment_done
-> timer_mem reset
```

이 구조는 본질적으로 deterministic counter이지만, 회로 해석은 sample tick spike를
timer neuron membrane에 적분하고 threshold 도달 시 boundary spike를 내는 방식이다.

## 7. Snapshot C24 모델

Snapshot C24는 60초 AFE+ADC ECG stream을 받아 NSR / CHF / ARR / AFF 중 하나를
출력하는 SNN-inspired RTL classifier이다.

입력과 출력:

| 항목 | 정의 |
| --- | --- |
| input | 1 kSPS signed 12-bit `adc_data` |
| snapshot length | 60초 |
| output class | NSR / CHF / ARR / AFF |
| output signal | `pred_class`, `class_mem_*`, feature count/debug |
| readout | class membrane WTA |

Snapshot C24는 feature vector classifier가 아니라, feature spike가 class neuron
membrane에 fixed signed weight로 누적되는 구조다.

```text
if feature_evidence_spike:
    class_mem[NSR] += W_FEATURE_TO_NSR
    class_mem[CHF] += W_FEATURE_TO_CHF
    class_mem[ARR] += W_FEATURE_TO_ARR
    class_mem[AFF] += W_FEATURE_TO_AFF

segment_done:
    pred_class = argmax(class_mem)
```

### 7.1 Adaptive QRS LIF

Adaptive QRS LIF는 ECG stream에서 QRS complex에 해당하는 강한 slope event를
검출한다. `adc_data[n] - adc_data[n-1]`의 절댓값을 보고 strong event를 만들며,
초기 2000 sample 동안 threshold bank를 calibration한다.

주요 파라미터:

| 항목 | 값 |
| --- | ---: |
| calibration samples | 2000 |
| adaptive min event threshold | 4 |
| adaptive target event count | 100 |
| QRS event weight | 8 |
| QRS threshold | 16 |
| refractory | 280 ms |

출력 `beat_spike`는 pNN, RDM, RAM, ECP, QRS MAF, RBBB feature의 timing 기준이다.

### 7.2 pNN125 Rhythm Predictor

pNN125는 RR interval이 예측 가능한 rhythm window 안에 들어오는지 판단한다.
250 ms부터 2500 ms까지 50 ms 간격의 RR hypothesis neuron bank를 두고, 다음 beat가
예상 window 안에 들어오면 match, 벗어나면 mismatch evidence를 만든다.

| 항목 | 값 |
| --- | ---: |
| RR base delay | 250 ms |
| RR step | 50 ms |
| hypothesis count | 46 |
| prediction half window | 125 ms |

pNN mismatch는 ARR/AFF 계열 irregular rhythm evidence로 사용된다.

### 7.3 RDM

RDM은 연속 RR interval의 변화량을 직접 측정한다.

```text
rr_diff = abs(RR_curr - RR_prev)
```

10 ms, 20 ms, ..., 150 ms threshold bank를 두고, threshold를 넘는 level spike를
count한다. pNN이 예측 window를 보는 feature라면, RDM은 실제 RR 변화량을 보는
feature다.

### 7.4 DSCR

DSCR은 raw ADC stream에서 slope sign-change를 측정한다. ECG waveform의 morphology
complexity를 잡기 위한 feature이며, rhythm irregularity보다 NSR/CHF 계열의
morphology 분리에 더 가깝다.

구조:

```text
valid_slope_spike = abs(delta) >= slope_threshold
sign_flip_spike = current_slope_sign != previous_slope_sign
```

### 7.5 RAM

RAM은 R-peak amplitude response를 threshold bank code로 변환한다. 여기서 RAM은
Random Access Memory가 아니라 R-peak Amplitude Mean 계열 feature이다.

R peak 주변 amplitude를 관찰하고, amplitude bank를 통과한 code를 누적한다. 실제
평균 division은 RTL에서 수행하지 않고, code sum/count와 threshold/gate를 사용한다.

### 7.6 ECP

ECP는 ectopic beat에서 나타날 수 있는 early beat와 compensatory pause pattern을
감지한다.

```text
early RR detected
-> pending state
-> next RR pause detected
-> ectopic_pair_spike
```

ARR 쪽 ectopic rhythm evidence로 사용된다.

### 7.7 QRS MAF

QRS MAF는 QRS morphology abnormality를 잡는다. QRS width, slope complexity,
energy/area deviation 등을 counter와 comparator로 계산한다.

주요 evidence:

```text
qrs_maf_count
qrs_width_abn_count
qrs_complex_abn_count
qrs_energy_abn_count
```

### 7.8 RBBB QRS Delay Bank

RBBB QRS Delay Bank는 regular rhythm처럼 보이지만 QRS conduction delay 성격이
반복되는 snapshot을 보조적으로 잡기 위한 feature다. 이는 임상적 RBBB 진단기가
아니라, RBBB-like conduction delay proxy이다.

C24 최종 파라미터:

| 항목 | 값 |
| --- | ---: |
| low slope threshold | 5 |
| wide threshold | 120 |
| terminal threshold | 4 |
| repeat threshold | 5 |
| NSR inhibition | 100000 |
| ARR boost | 100000 |

### 7.9 EERG

EERG는 RBBB delay evidence는 없지만 episodic ectopic 또는 boundary abnormal 성격을
보이는 ARR-like snapshot을 rescue하기 위한 gate다.

조건:

```text
rbbb_like_beat_count == 0
pre_qrs_bump_count >= 1
early_count >= 10 OR ECP_count >= 3
pNN_mismatch_rate <= 0.15
RDM_avg <= 5
```

활성화되면 ARR membrane에 boost를 넣는다.

### 7.10 Class Score Neurons / C24 Readout

`class_score_neurons.v`는 각 feature evidence를 4개 class membrane으로 누적한다.
C24 readout은 Python global readout을 그대로 matrix multiplication block으로 넣은
것이 아니라, Python C24 coefficient를 feature spike/count별 signed integer weight로
fold하여 RTL class membrane에 이식한 구조다.

초기 문제:

| 항목 | test 성능 |
| --- | ---: |
| Python C24 global readout | 193 / 240 = 80.42% |
| 기존 RTL raw WTA | 174 / 240 = 72.50% |

해결 방향:

```text
Python:
    score[class] += feature_count * coef[class]

RTL:
    if feature_spike_or_count_event:
        class_mem[class] += folded_integer_weight
```

normalization, count scale, base scale, bias correction은 integer folded weight와
integer bias로 흡수했다. 최종 RTL은 `c24_mem_nsr/chf/arr/aff`를 64-bit signed
membrane으로 유지하고, `segment_done`에서 WTA를 수행한다.

## 8. Snapshot C24 후보군 C01-C32

Snapshot C24를 선택하기 위해 C01-C32 후보군을 구성했다. 이는 feature 자체를 새로
만드는 탐색이 아니라, 같은 feature set 안에서 timing window, threshold, bank,
gate, boost, readout parameter를 바꾸는 후보군이다.

탐색 원칙:

1. train/validation 기준으로 후보를 선택한다.
2. test set은 최종 후보 확정 후 1회 평가한다.
3. record-wise split을 유지해 같은 record가 train/val/test에 섞이지 않게 한다.
4. segment accuracy뿐 아니라 macro-F1, balanced accuracy, class별 recall을 함께 본다.

후보군 요약:

| 후보 | 설명 |
| --- | --- |
| C01 | pNN window 100 ms + ECP 100 ms |
| C02 | pNN 90 ms + ECP 80 ms |
| C03 | pNN 110 ms + ECP 100 ms |
| C04 | pNN 140 ms + ECP 140 ms |
| C05 | pNN 150 ms + ECP 100 ms |
| C06 | pNN/ECP 100 ms + DSCR 민감화 + RAM low/mid 조정 |
| C07 | DSCR 엄격화 + RAM step 조밀화 |
| C08 | pNN 150 ms + DSCR 민감화 + RAM 조정 |
| C09 | pNN 90 ms + ECP 80 ms + RAM 조밀화 |
| C10 | RAM low-amplitude bank 강화 |
| C11 | RAM mid-low 영역 조밀화 |
| C12 | RAM 전체 조밀화 |
| C13 | RAM bank high-amplitude 이동 |
| C14 | DSCR slope threshold 5 |
| C15 | DSCR slope threshold 6 |
| C16 | DSCR slope threshold 10 |
| C17 | QRS MAF 민감 후보 |
| C18 | QRS MAF 중간 후보 |
| C19 | QRS MAF 엄격 후보 |
| C20 | rhythm 후보 + QRS MAF 중간 조합 |
| C21 | RBBB QRS delay 매우 민감 |
| C22 | RBBB QRS delay 민감 |
| C23 | RBBB baseline 근처 + 강한 ARR boost/NSR inhibition |
| C24 | RBBB 조건 엄격 + 약한 boost |
| C25 | pNN/ECP + 민감한 RBBB delay |
| C26 | EERG permissive |
| C27 | EERG strict |
| C28 | EERG permissive + 강한 ARR boost |
| C29 | pNN/ECP + RBBB delay + EERG 조합 |
| C30 | adaptive QRS front-end 민감 |
| C31 | adaptive QRS front-end 엄격 |
| C32 | adaptive QRS target count 낮춤 + pNN/ECP 조합 |

Validation ranking:

| Rank | Candidate | Val Acc | Val Macro-F1 | Val Balanced Acc |
| ---: | --- | ---: | ---: | ---: |
| 1 | C24 | 91.25% | 91.18% | 91.34% |
| 2 | C09 | 90.42% | 90.29% | 90.35% |
| 3 | C07 | 90.00% | 89.93% | 89.99% |
| 4 | C20 | 89.58% | 89.54% | 89.71% |
| 5 | C16 | 88.75% | 88.62% | 88.89% |

C24 최종 parameter:

| 항목 | 값 |
| --- | --- |
| candidate | C24 |
| QRS tag | `e5w8t16l0r280a1b1c2000tc100_c24` |
| profile | compact |
| count scale | 10.0 |
| base scale | 25000.0 |
| L2 | 1000.0 |
| class boost | NSR 1.1, CHF 1.8, ARR 1.8, AFF 1.0 |
| RBBB low slope th | 5 |
| RBBB wide th | 120 |
| RBBB terminal th | 4 |
| RBBB repeat th | 5 |
| RBBB NSR inhibition | 100000 |
| RBBB ARR boost | 100000 |

## 9. Snapshot C24 성능

60초 AFE+ADC snapshot dataset 기준 C24 성능:

| Split | Accuracy | Macro-F1 | Balanced Accuracy |
| --- | ---: | ---: | ---: |
| train | 434 / 480 = 90.42% | 90.28% | 90.22% |
| validation | 219 / 240 = 91.25% | 91.18% | 91.34% |
| test | 193 / 240 = 80.42% | 80.28% | 79.99% |

Test confusion matrix:

| Actual \ Pred | NSR | CHF | ARR | AFF |
| --- | ---: | ---: | ---: | ---: |
| NSR | 50 | 12 | 2 | 0 |
| CHF | 7 | 56 | 0 | 1 |
| ARR | 14 | 2 | 34 | 4 |
| AFF | 0 | 3 | 2 | 53 |

해석:

1. AFF와 CHF는 비교적 안정적으로 잡힌다.
2. ARR은 NSR로 흡수되는 경우가 가장 큰 병목이다.
3. Snapshot 하나만으로 환자 상태를 확정하는 것은 한계가 있다.
4. 따라서 Snapshot C24 뒤에 Final Membrane Layer를 붙여 장시간 evidence pattern을 누적한다.

## 10. 30분 Final Membrane Layer 설계

Final Membrane Layer는 60초 Snapshot C24 뒤에 붙는 readout layer이다. Snapshot C24의
feature threshold, weight, gate, boost는 고정하고, Final Membrane만 train/validation
기준으로 탐색했다.

30분 chunk 처리:

```text
30분 chunk = 1,800,000 samples at 1 kSPS
-> 60초 snapshot 30개
-> 각 snapshot마다 Snapshot C24 pred_class 출력
-> pred_class를 one-hot spike로 해석
-> chunk class membrane에 누적
```

`rtl/final_membrane_layer.v`:

```text
if snapshot_done and pred_valid:
    pred_count[pred_class] += 1

if chunk_done:
    chunk_pred = argmax(pred_count_NSR, pred_count_CHF, pred_count_ARR, pred_count_AFF)
```

record-level 처리:

```text
같은 record에 속한 30분 chunk들의 pred_count를 다시 누적
record_done 시점에 최종 WTA
```

`rtl/record_level_final_membrane_layer.v` 최종 rule:

```text
score_NSR = accumulated_count_NSR
score_CHF = accumulated_count_CHF
score_ARR = accumulated_count_ARR
score_AFF = accumulated_count_AFF

if accumulated_count_ARR >= 5:
    score_ARR += 16

patient_pred = WTA(score_NSR, score_CHF, score_ARR, score_AFF)
tie order = NSR, CHF, ARR, AFF
```

이 rule은 단순 majority vote에 ARR rescue membrane을 추가한 구조다. Snapshot C24에서
ARR이 NSR로 일부 흡수되는 문제가 있었기 때문에, record 전체에서 ARR snapshot spike가
5개 이상 반복되면 ARR membrane에 추가 current를 주도록 설계했다.

## 11. Final Membrane 탐색 방법

Python 등가모델을 사용해 Final Membrane 후보를 탐색했다.

입력:

```text
results/final_membrane_30min_recordwise/snapshot_dump_train.csv
results/final_membrane_30min_recordwise/snapshot_dump_val.csv
results/final_membrane_30min_recordwise/snapshot_dump_test.csv
```

탐색 원칙:

1. Snapshot C24 내부 parameter는 고정한다.
2. test set은 후보 선택에 사용하지 않는다.
3. train/validation만으로 final membrane parameter를 선택한다.
4. validation-selected 후보 1개에 대해 test를 마지막 1회 평가한다.
5. 전체 accuracy뿐 아니라 macro-F1, balanced accuracy, class별 recall을 본다.
6. RTL 구현 가능성이 낮은 복잡한 model은 배제한다.

탐색 후보:

| 후보군 | 설명 |
| --- | --- |
| record snapshot count | record 전체 snapshot pred count majority |
| record mem sum | Snapshot C24 class membrane sum 기반 |
| weighted count | class별 count weight/bias |
| ARR rescue | ARR count threshold 이상이면 ARR boost |
| AFF rescue | AFF/irregularity threshold 기반 AFF boost |

최종 strict selection:

| 항목 | 값 |
| --- | --- |
| selected candidate id | 15013 |
| kind | `record_arr_rescue` |
| arr threshold | 5 |
| abnormal threshold | 0 |
| ARR boost | 16 |
| tie order | NSR, CHF, ARR, AFF |
| eligible candidates | 105 |

## 12. Final Membrane 성능

Python 등가모델 결과:

| Split | Accuracy | Macro-F1 | Balanced Accuracy |
| --- | ---: | ---: | ---: |
| train | 55 / 68 = 80.88% | 80.19% | 80.88% |
| validation | 29 / 32 = 90.62% | 90.28% | 90.62% |
| test | 30 / 36 = 83.33% | 83.11% | 83.33% |

XSim RTL 결과:

| Split | Accuracy | Macro-F1 | Balanced Accuracy | Python-vs-XSim mismatch |
| --- | ---: | ---: | ---: | ---: |
| train | 55 / 68 = 80.88% | 80.19% | 80.88% | 0 |
| validation | 29 / 32 = 90.62% | 90.28% | 90.62% | 0 |
| test | 30 / 36 = 83.33% | 83.11% | 83.33% | 0 |

Test per-class metrics:

| Class | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| NSR | 80.00% | 88.89% | 84.21% | 9 |
| CHF | 85.71% | 66.67% | 75.00% | 9 |
| ARR | 100.00% | 77.78% | 87.50% | 9 |
| AFF | 75.00% | 100.00% | 85.71% | 9 |

Test confusion matrix:

| Actual \ Pred | NSR | CHF | ARR | AFF |
| --- | ---: | ---: | ---: | ---: |
| NSR | 8 | 1 | 0 | 0 |
| CHF | 0 | 6 | 0 | 3 |
| ARR | 2 | 0 | 7 | 0 |
| AFF | 0 | 0 | 0 | 9 |

정리 후 XSim 재검증:

```text
test split 재실행: 30 / 36 = 83.33%
Python-vs-XSim mismatch: 0 / 36
combined compare: 136 rows, mismatch 0
```

## 13. RTL/XSim 검증

XSim testbench:

```text
sim/tb_snn_ecg_30min_record_level_dataset.v
```

실행 script:

```text
scripts/run_record_level_strict_xsim.py
```

검증 방식:

1. Python prediction CSV에서 XSim manifest를 생성한다.
2. 실제 30분 `.mem` chunk를 RTL testbench에 stream으로 입력한다.
3. chunk마다 1,800,000 sample을 구동한다.
4. 60초마다 Snapshot C24가 `pred_class`를 낸다.
5. 30개 snapshot이 끝나면 chunk vote membrane이 나온다.
6. 같은 record의 chunk들을 record-level membrane에 누적한다.
7. record_done 시점에 최종 class를 출력한다.
8. XSim output CSV와 Python output CSV를 case_id 단위로 비교한다.

최종 결론:

```text
Python final membrane equivalent == RTL/XSim final membrane
prediction mismatch: 0 / 136
```

## 14. 합성 자원 사용량

Vivado 2020.2, `xc7a100tcsg324-1`, synthesis-only `report_utilization` 기준이다.

| Design | LUT | FF | BRAM36 | BRAM18 | DSP |
| --- | ---: | ---: | ---: | ---: | ---: |
| `record_level_final_membrane_layer` | 142 | 132 | 0 | 0 | 0 |
| `final_membrane_layer` | 52 | 27 | 0 | 0 | 0 |
| final membrane chain | 163 | 157 | 0 | 0 | 0 |
| Snapshot C24 30분 top | 20,147 | 2,129 | 0 | 0 | 0 |
| full top + record final membrane | 20,256 | 2,259 | 0 | 0 | 0 |

record-level final membrane 추가 비용:

```text
+109 LUT
+130 FF
+0 DSP
+0 BRAM
```

해석:

1. 최종 membrane layer는 Snapshot C24 feature/readout core에 비해 매우 작다.
2. DSP와 BRAM을 사용하지 않는다.
3. 자원 대부분은 Snapshot C24 내부 feature block과 class score neurons에서 발생한다.
4. Final Membrane은 counter/accumulator/comparator 중심이라 하드웨어 비용이 낮다.

## 15. 전력 소모량 상태

현재 저장소에는 mW 단위의 최종 전력 보고서가 없다. 따라서 본 보고서에서 정량 전력
수치를 임의로 제시하지 않는다.

현재 확인된 저전력 관련 근거:

| 항목 | 상태 |
| --- | --- |
| floating point | 사용 안 함 |
| divider | 사용 안 함 |
| DSP multiplier | 0 |
| BRAM | 0 |
| Final Membrane incremental LUT | +109 |
| Final Membrane incremental FF | +130 |

정량 전력을 보고하려면 다음 절차가 필요하다.

1. target board/part와 clock constraint를 확정한다.
2. post-synthesis 또는 post-implementation netlist를 만든다.
3. 실제 switching activity를 VCD/SAIF로 추출하거나 activity rate를 합리적으로 설정한다.
4. Vivado `report_power`를 실행한다.
5. static power, dynamic power, clock/network/logic power를 분리해 보고한다.

따라서 현재 단계에서 정확한 표현은 다음이다.

```text
전력 소모량: 정량 미측정.
다만 최종 RTL은 DSP 0, BRAM 0, integer counter/comparator/accumulator 기반으로
구성되어 Final Membrane 추가 비용은 +109 LUT / +130 FF 수준이다.
```

## 16. 최종 파일 구성

현재 정리된 repository에서 핵심 파일은 다음과 같다.

```text
README.md
FINAL_REPORT_KR.md

rtl/
  final_membrane_layer.v
  record_level_final_membrane_layer.v
  snn_ecg_30min_final_top.v
  core/*.v

sim/
  tb_snn_ecg_30min_record_level_dataset.v

scripts/
  snapshot_c24_rtl_exact.py
  final_membrane_30min_recordwise_pipeline.py
  search_final_membrane_30min_recordwise.py
  search_final_membrane_30min_recordwise_recordlevel.py
  search_final_membrane_30min_recordwise_recordlevel_strict.py
  run_record_level_strict_xsim.py

fullrec_afe_30min_annotation_valid_balanced/
  annotation_valid_balanced_30min_manifest.csv
  train/
  val/
  test/

results/final_membrane_30min_recordwise/
  snapshot_dump_train.csv
  snapshot_dump_val.csv
  snapshot_dump_test.csv
  no_oracle_record_level_strict_selected_params.json
  no_oracle_record_level_strict_*_metrics.json
  no_oracle_record_level_strict_*_predictions.csv
  xsim_record_level_strict_*_metrics.json
  xsim_record_level_strict_*_predictions.csv
  python_vs_xsim_record_level_strict_compare.csv
  record_level_strict_rtl_xsim_report.md
  synth/final_membrane_resource_report.md
```

## 17. 한계와 향후 개선

현재 한계:

1. ARR 원천 데이터가 30분 excerpt 중심이라 24시간 Holter-style full-record 검증이 어렵다.
2. AFF는 record 수가 4개로 제한되어 record diversity가 낮다.
3. CHF는 record-level disease label이며, beat annotation만으로 CHF-specific rhythm을 직접 증명하기 어렵다.
4. Snapshot C24의 ARR 일부가 NSR로 흡수되는 문제가 남아 있다.
5. 정량 전력 보고서가 아직 없다.
6. 현재 Final Membrane은 단순하고 해석 가능한 rule 기반이며, 더 풍부한 abnormal evidence를 쓰는 layer는 추가 검증이 필요하다.

향후 개선:

1. 24시간 이상 annotation-rich ARR/AFF/NSR/CHF dataset 확보
2. 더 균형 잡힌 record-level split 구성
3. Final Membrane에 abnormal evidence count, RBBB/EERG persistence, CHF morphology persistence 반영
4. Snapshot C24 stage별 Python-vs-RTL bit-exact 검증 강화
5. Vivado implementation 및 `report_power` 추가
6. board-level timing, resource, power, throughput 통합 보고
7. clinical label과 rhythm annotation의 차이를 명확히 분리한 evaluation protocol 작성

## 18. 최종 결론

본 프로젝트는 ECG stream을 60초 단위로 반복 평가하고, 그 결과를 장시간 membrane에
누적해 최종 class를 판정하는 SNN-inspired hierarchical ECG classifier를 구현했다.

핵심 성과:

1. AFE+ADC signed 12-bit stream을 직접 입력으로 하는 RTL pipeline을 구성했다.
2. 60초 Snapshot C24 classifier를 feature spike to class membrane 구조로 구현했다.
3. C01-C32 후보 탐색을 통해 C24를 선택했다.
4. Python C24 readout과 RTL raw WTA 차이를 C24 folded integer membrane 구조로 보정했다.
5. 30분 annotation-valid balanced dataset을 구성했다.
6. Final Membrane Layer를 Python에서 train/validation 기준으로 선택했다.
7. 선택된 Final Membrane을 RTL로 구현하고 XSim으로 검증했다.
8. XSim test accuracy 83.33%를 달성했다.
9. Python-vs-XSim prediction mismatch 0 / 136을 확인했다.
10. 최종 구조는 DSP 0, BRAM 0이며, Final Membrane 추가 비용은 +109 LUT / +130 FF이다.

최종적으로 본 시스템은 단일 60초 ECG snapshot을 환자 진단으로 단정하는 모델이 아니라,
긴 ECG stream에서 반복적으로 생성되는 snapshot-level class evidence를 SNN-style
membrane에 누적하여 최종 class를 판정하는 계층형 ECG classifier이다.

## 19. 참고문헌 및 데이터 출처

1. ISHNE/HRS Expert Consensus Statement on Ambulatory ECG and External Cardiac Monitoring/Telemetry, Heart Rhythm Society, 2017.  
   https://www.hrsonline.org/resource/2017-ishne-hrs-expert-consensus-statement/

2. Holter Monitor, StatPearls, NCBI Bookshelf.  
   https://www.ncbi.nlm.nih.gov/books/NBK538203/

3. MIT-BIH Arrhythmia Database, PhysioNet.  
   https://physionet.org/content/mitdb/1.0.0/

4. MIT-BIH Normal Sinus Rhythm Database, PhysioNet.  
   https://physionet.org/content/nsrdb/1.0.0/

5. BIDMC Congestive Heart Failure Database, PhysioNet.  
   https://physionet.org/content/chfdb/1.0.0/

6. MIT-BIH Atrial Fibrillation Database, PhysioNet.  
   https://physionet.org/content/afdb/1.0.0/

7. PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals.  
   Goldberger et al., Circulation, 2000. PhysioNet citation page included in each PhysioNet database page above.
