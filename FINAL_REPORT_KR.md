# AFE+ADC XMODEL 연동 SNN 기반 장시간 ECG 4-Class Classification Accelerator IP Core 설계 최종 보고서

## 1. 요약

본 프로젝트는 공개 digitized ECG record를 analog-equivalent `vin`으로 재구성하고, AFE+ADC XMODEL을 통과시켜 signed 12-bit stream을 생성한 뒤, 이를 SNN-inspired ECG Classification Accelerator IP Core에 입력하여 NSR/CHF/ARR/AFF 4-class 장시간 ECG classification을 수행하는 FPGA/VLSI engineering prototype이다.

최종 모델은 `structural_guarded_silent_aff_1008710`이며, 60초 Snapshot Readout은 고정하고 30분 Final Membrane Readout을 strict record-wise train/validation 기준으로 확정했다. Locked final_test는 모델 선택, 파라미터 탐색, 외부 논의 문맥에 사용하지 않았고, 확정 이후 1회만 평가했다. 최종 성능은 final_test 30분 청크 29/36 = 80.56%, record-majority 16/19 = 84.21%이다.

RTL/XSim, Vivado 구현, AXI/IP-XACT 패키징, Vitis/MicroBlaze full-record replay flow를 통해 engineering validation을 수행했다. 단, 본 결과는 직접 전극 측정, board-level AFE/ADC silicon 측정, transistor-level layout 검증, 의료 진단 유효성 검증을 의미하지 않는다.

## 2. 연구 배경과 목표

ECG rhythm classification은 단일 sample이나 짧은 beat 단위만으로 안정적으로 결정되기 어렵다. NSR, CHF, ARR, AFF는 리듬 변동성, 파형 형태 이상, QRS evidence, 장시간 추세가 함께 반영되어야 한다. 따라서 본 프로젝트는 dense CNN/RNN classifier를 FPGA에 그대로 올리는 대신, ECG domain evidence를 spike/event 형태로 압축하고 30분 window에서 final membrane을 누적하는 streaming accelerator 구조를 선택했다.

목표는 높은 resource를 요구하는 multiply-heavy model이 아니라, signed 12-bit ECG stream을 직접 처리하고 counter, comparator, signed accumulator, WTA 기반으로 동작하는 low-resource biomedical accelerator IP를 구현하는 것이다.

## 3. 전체 시스템 Flow

```mermaid
flowchart LR
    A["공개 digitized ECG record"] --> B["analog-equivalent vin reconstruction"]
    B --> C["AFE+ADC XMODEL"]
    C --> D["signed 12-bit .mem stream"]
    D --> E["60초 Snapshot Readout"]
    E --> F["30분 Final Membrane Readout"]
    F --> G["NSR / CHF / ARR / AFF"]
    F --> H["RTL / XSim / Vivado / IP-XACT / Vitis"]
```

전체 flow는 공개 digitized ECG record에서 시작한다. 입력 code는 `vin_v = code / 200000` 기준으로 voltage-equivalent waveform으로 해석하고, AFE+ADC XMODEL을 통해 signed 12-bit `.mem` stream으로 변환한다. 이 stream은 RTL/IP에 입력되어 60초 snapshot evidence를 만들고, 30분 Final Membrane Readout에서 class별 membrane을 누적한 뒤 WTA로 최종 class를 출력한다.

## 4. AFE+ADC XMODEL 입력 생성

공개 ECG dataset은 이미 digitized record이므로 원래의 sensor waveform을 복원할 수 없다. 본 프로젝트는 이를 direct acquisition으로 주장하지 않고, virtual DAC/PWL-equivalent reconstruction으로 해석한다.

AFE+ADC nominal chain은 다음과 같이 정리한다.

| 단계 | 역할 |
|---|---|
| `code / 200000` | digitized ECG code를 analog-equivalent `vin`으로 해석 |
| HPF | baseline drift 저감 |
| IA gain x201 | ECG amplitude scaling |
| 60 Hz notch | 전원선 성분 억제 |
| LPF 150 Hz | 고주파 잡음 제한 |
| 12-bit ADC quantization | RTL 입력 signed 12-bit stream 생성 |

이 flow는 model-based mixed-signal-to-digital verification이다. Board-level AFE 측정, ADC silicon 측정, transistor-level layout 결과는 포함하지 않는다.

## 5. Snapshot SNN Readout

Snapshot Readout은 60초 window마다 ECG evidence를 spike/counter 형태로 압축한다. 주요 feature block은 QRS detection, rhythm prediction/mismatch evidence, morphology evidence, variability evidence, ectopic/abnormal evidence를 포함한다. Snapshot 내부에서는 class membrane과 WTA를 통해 60초 단위 class evidence를 만든다.

최종 제출에서는 locked Final Membrane에 입력되는 고정 Snapshot Readout 구조를 기준으로 설명한다.

### 5.1 Feature block을 왜 나누는가

ECG 4-class classification에서 한 sample의 크기만으로는 NSR, CHF, ARR, AFF를 구분하기 어렵다. 같은 30분 record 안에서도 어떤 60초 구간은 정상처럼 보일 수 있고, 어떤 구간은 rhythm 또는 morphology abnormality가 뚜렷할 수 있다. 그래서 본 설계는 sample stream을 바로 class로 바꾸지 않고, 다음 세 종류의 evidence로 나누어 누적한다.

| Evidence 종류 | 보는 대상 | 직관적 의미 |
|---|---|---|
| Beat/QRS evidence | QRS 위치, R peak, QRS 폭 | “심장이 한 번 뛴 위치와 그 beat 모양이 정상적인가” |
| Rhythm evidence | RR interval, 예측 beat 위치, variability | “박동 간격이 규칙적인가, 갑자기 흔들리는가” |
| Morphology evidence | slope sign flip, energy, terminal activity | “파형이 단순한가, 넓거나 복잡하거나 늦게 끌리는가” |

이 evidence는 모두 integer counter, comparator, signed accumulator로 구현된다. 따라서 floating-point convolution, recurrent state matrix, multiplier-heavy dense layer가 필요 없다.

### 5.2 Adaptive event encoder와 QRS LIF detector

심전도에서 가장 먼저 잡아야 하는 것은 QRS파이다. QRS는 R peak 주변에서 짧은 시간 동안 기울기가 크게 변한다. 따라서 RTL은 파형 전체를 한 번에 해석하기 전에, 먼저 강한 상승/하강 event를 만드는 adaptive event encoder를 둔다.

1단계는 event encoder이다.

```text
현재 sample과 이전 sample을 뺀다.
delta = adc_data[n] - adc_data[n-1]

abs(delta)가 adaptive threshold보다 크면 strong_event가 발화한다.
delta가 양수이면 up_event 성격이고,
delta가 음수이면 down_event 성격이다.
```

이 `strong_event`는 ECG에서 “갑자기 크게 움직인 순간”을 의미한다. QRS 구간에서는 이런 strong event가 짧은 시간 안에 연속해서 나타난다. 반대로 baseline drift나 작은 잡음은 threshold와 leak 구조를 통과하지 못하게 설계했다.

2단계는 QRS LIF detector이다. QRS LIF는 `strong_event`를 바로 beat로 확정하지 않고, membrane에 누적해서 본다.

```text
strong_event 발생
-> QRS LIF membrane에 QRS_W_EVENT만큼 흥분성 자극 입력

strong_event가 없는 clock
-> QRS LIF membrane에서 QRS_LEAK만큼 손실

QRS LIF membrane >= QRS_TH
-> beat_spike 발화
-> QRS LIF membrane reset
-> refractory counter 시작
```

즉 QRS LIF neuron은 단발성 noise 하나에는 잘 반응하지 않는다. 그러나 QRS 구간처럼 `strong_event`가 연속해서 들어오면 membrane이 임계값을 넘는다. 그 순간의 `beat_spike`가 “QRS 하나를 찾았다”는 event이다.

`refractory`는 같은 QRS를 여러 번 세지 않기 위한 억제 장치이다. 한 번 `beat_spike`가 발생하면 일정 시간 동안 QRS membrane을 0으로 유지하고 재발화를 막는다. 또한 segment 시작부의 calibration 구간에서는 record마다 다른 amplitude와 noise 수준을 반영해 event threshold를 맞춘다.

주요 RTL 파일:

```text
rtl/core/ecg_event_encoder_adaptive.v
rtl/core/qrs_lif_detector.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `ADAPT_QRS_CALIB_SAMPLES` | 2000 sample, segment 시작부 adaptive threshold calibration 길이 |
| `ADAPT_QRS_MIN_EVENT_TH` | 4, adaptive event threshold 하한 |
| `ADAPT_QRS_TARGET_EVENT_COUNT` | 100, calibration 중 목표 event 수 |
| `QRS_W_EVENT` | 8, strong event가 QRS membrane에 주는 흥분성 자극 |
| `QRS_LEAK` | 0, QRS membrane의 clock별 손실 |
| `QRS_TH` | 16, QRS neuron 발화 임계값 |
| `QRS_REF` | 280 sample, beat 발화 후 재발화 억제 시간 |

이 QRS LIF의 출력 `beat_spike`는 뒤 feature들의 기준 clock이 된다. PNN, RDM, RAM, ECP, QRS MAF, RBBB-like delay block은 모두 이 beat spike를 중심으로 “박동 간격”, “박동 주변 amplitude”, “QRS 폭”, “terminal activity”를 관찰한다.

### 5.3 PNN rhythm predictor

PNN은 “다음 박동이 언제 올지 예측하고, 실제 박동이 그 예측을 지켰는지”를 보는 rhythm neuron이다. 여기서 중요한 점은 winner가 단순한 출력값이 아니라, 다음 beat 판단의 기준으로 저장된다는 것이다.

목표는 다음과 같다.

```text
RR interval이 일정하게 반복되는가?
직전 rhythm으로 예측한 다음 beat 위치에 실제 beat가 들어왔는가?
```

PNN 내부에는 여러 개의 RR hypothesis neuron이 있다.

```text
hypothesis 0: 250 ms
hypothesis 1: 300 ms
hypothesis 2: 350 ms
...
hypothesis 45: 2500 ms
```

각 hypothesis neuron은 “RR interval이 이 정도일 것이다”라는 후보이다. QRS LIF가 `beat_spike`를 내면, PNN은 지난 beat부터 이번 beat까지 흐른 시간 `token_age`를 현재 RR interval로 본다.

동작 순서는 다음과 같다.

```text
1. beat_spike가 들어온다.
2. 지난 beat 이후 흐른 token_age를 현재 RR interval로 확정한다.
3. 46개 RR hypothesis neuron 중 현재 RR과 가장 가까운 neuron을 찾는다.
4. 그 neuron이 current_winner가 된다.
5. current_winner는 predictor_id로 저장되어 다음 beat의 기준이 된다.
6. 다음 beat가 오면, 이번 RR을 직전 predictor_id의 중심값과 비교한다.
7. 차이가 WINDOW_HALF 이내이면 pnn_match_spike 발화.
8. 차이가 WINDOW_HALF 밖이면 pnn_mismatch_spike 발화.
```

정확히는 이번 beat에서 match/mismatch를 판단할 때 사용하는 기준은 직전 beat에서 저장된 `predictor_id`이다. 이번 RR로 새로 선택한 `current_winner`는 다음 beat를 평가할 `predictor_id`로 저장된다. 첫 valid RR은 predictor를 설정하는 용도이므로, match/mismatch 판정은 이전 predictor가 존재한 뒤부터 유효하다.

따라서 PNN의 핵심은 다음 문장이다.

```text
현재 RR의 winner neuron이 다음 RR을 평가할 predictor neuron으로 넘어간다.
```

예를 들어 현재 RR이 800 ms 근처라면 800 ms hypothesis가 winner가 된다. 그러면 PNN은 다음 beat도 약 800 ms 근처에 올 것이라고 기대한다. 다음 beat가 790 ms에 오면 match이고, 500 ms나 1200 ms에 오면 mismatch이다.

해석:

- `pnn_match_spike`: rhythm이 직전 winner가 만든 예측을 지켰다는 발화
- `pnn_mismatch_spike`: rhythm이 직전 winner 예측에서 벗어났다는 발화
- match가 많으면 비교적 규칙적인 rhythm evidence
- mismatch가 반복되면 ARR/AFF 계열 irregular rhythm evidence

주요 RTL 파일:

```text
rtl/core/pnn_rhythm_predictor.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `BASE_DELAY` | 250 sample, 첫 RR hypothesis 중심값 |
| `DELAY_STEP` | 50 sample, hypothesis 간격 |
| `NUM_HYP` | 46개 hypothesis neuron |
| `WINDOW_HALF` | 125 sample, predictor와 실제 RR을 match로 볼 허용 반경 |

### 5.4 RDM variability neuron

RDM은 PNN보다 직접적으로 RR interval 변화량을 본다. PNN이 “예측 위치를 지켰는가”를 본다면, RDM은 “이번 RR과 직전 RR이 얼마나 달라졌는가”를 level/code로 만든다.

목표는 다음과 같다.

```text
연속된 beat 간격이 안정적인가?
아니면 beat마다 RR interval이 크게 흔들리는가?
```

동작은 단순하지만, RTL 구현은 threshold bank 형태이다.

```text
beat_spike로 RR interval이 확정된다.
현재 RR과 직전 RR을 비교한다.

rr_diff = abs(RR_curr - RR_prev)

rr_diff가 10 sample 이상이면 level 1 neuron 발화
rr_diff가 20 sample 이상이면 level 2 neuron 발화
...
rr_diff가 150 sample 이상이면 level 15 neuron 발화
```

즉 RDM은 하나의 floating-point variability 값을 계산하는 block이 아니라, 여러 threshold neuron이 계단처럼 배치된 구조이다. 변화량이 작으면 낮은 level까지만 발화하고, 변화량이 크면 높은 level neuron까지 발화한다.

해석:

- `rr_diff_valid_spike`: 이번 beat에서 RR 변화량 측정이 유효하다는 발화
- `rdm_level_spike`: 변화량 threshold bank 중 어느 level들이 켜졌는지 나타내는 bit vector
- `rdm_level_code`: 가장 높은 발화 level을 code로 표현한 값
- 낮은 RDM code 반복: 안정적인 rhythm
- 높은 RDM code 반복: beat-to-beat variability가 큰 rhythm

RDM evidence는 AFF처럼 RR interval이 불규칙하게 흔들리는 경우, 또는 ARR 구간에서 짧게 튀는 rhythm burst를 잡는 보조 evidence로 사용된다.

주요 RTL 파일:

```text
rtl/core/rdm_variability_neuron.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `DIFF_TH0`..`DIFF_TH14` | 10부터 150 sample까지 10 sample 간격의 RR 변화량 threshold bank |
| `AGE_WIDTH` | 12-bit RR interval counter width |

### 5.5 DSCR spike counter

DSCR은 beat 간격이 아니라 waveform shape를 본다. ECG가 매끈하게 지나가는지, 아니면 slope 방향이 자주 바뀌는 복잡한 morphology를 보이는지 세는 block이다.

목표는 다음과 같다.

```text
파형이 단순하고 매끈한가?
아니면 상승/하강 기울기가 자주 바뀌는 복잡한 morphology인가?
```

DSCR은 먼저 ECG를 leaky filter로 부드럽게 만든다. 그 다음 현재 filter 값의 변화량을 slope input으로 본다.

```text
filtered ECG 계산
slope_input = filtered[n] - filtered[n-1]
```

그 다음 두 개의 slope membrane을 둔다.

```text
positive slope membrane:
    상승 기울기 자극을 누적
    시간이 지나면 leak 발생
    충분히 큰 상승 기울기가 쌓이면 valid_slope_spike 발화

negative slope membrane:
    하강 기울기 자극을 누적
    시간이 지나면 leak 발생
    충분히 큰 하강 기울기가 쌓이면 valid_slope_spike 발화
```

이렇게 하면 아주 작은 흔들림은 leak에 의해 사라지고, 의미 있는 상승/하강만 slope spike가 된다.

그 다음 sign flip neuron이 있다.

```text
직전 valid slope가 상승이었고 이번 valid slope가 하강이면 sign flip 자극
직전 valid slope가 하강이었고 이번 valid slope가 상승이면 sign flip 자극
sign flip 자극이 threshold를 넘으면 dscr_sign_flip_spike 발화
```

해석:

- `dscr_valid_slope_spike`: 의미 있는 waveform slope가 감지되었다는 발화
- `dscr_sign_flip_spike`: 파형 기울기 방향이 의미 있게 바뀌었다는 발화
- slope/sign flip이 많으면 morphology가 복잡하거나 에너지가 많은 구간으로 해석된다.
- 이 evidence는 CHF/NSR 분리, AFF/ARR 보조 판단, QRS MAF와 연결된 morphology 판단에 쓰인다.

DSCR의 장점은 파형의 복잡도를 곱셈이나 주파수 변환 없이 counter와 threshold로 표현한다는 점이다.

주요 RTL 파일:

```text
rtl/core/dscr_spike_counter.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `FILTER_SHIFT` | leaky filter update scale |
| `SLOPE_LEAK` | slope membrane leak |
| `SLOPE_THRESHOLD` | valid slope 발화 threshold |
| `SIGN_WEIGHT` | sign flip membrane에 더하는 자극 |
| `SIGN_THRESHOLD` | sign flip 발화 threshold |

### 5.6 RAM peak accumulator

RAM은 memory block 이름이 아니라 R-peak amplitude response를 보는 feature block이다. QRS LIF가 beat를 찾으면, RAM은 beat 주변 window에서 baseline 대비 R peak가 얼마나 크게 올라갔는지 threshold bank로 본다.

목표는 다음과 같다.

```text
R peak의 amplitude가 어느 정도인가?
beat마다 amplitude response가 class별로 다르게 나타나는가?
```

동작은 다음과 같다.

```text
1. PNN predictor가 만든 beat 예상 window 주변에서 amplitude 관찰 window를 연다.
2. 각 sample에서 baseline을 뺀다.
3. baseline보다 위에 있는 양의 amplitude만 본다.
4. amplitude threshold bank를 통과한 정도를 code로 만든다.
5. window 안에서 가장 큰 code를 R peak amplitude code로 잡는다.
6. beat가 확인되면 ram_amp_spike와 ram_amp_code를 낸다.
```

예를 들어 threshold bank가 64, 96, 128, ...처럼 배치되어 있다면, R peak가 더 큰 beat는 더 높은 code를 만든다. RTL은 실제 전압 amplitude를 floating-point로 보존하지 않고, “이 beat의 peak response가 몇 번째 threshold까지 넘었는가”를 integer code로 누적한다.

해석:

- `ram_amp_spike`: R peak amplitude 측정이 유효하다는 발화
- `ram_amp_code`: amplitude threshold bank를 통과한 정도
- `ram_code_sum`: 60초 동안의 amplitude response 누적
- `ram_code_count`: amplitude가 측정된 beat 수

평균이나 나눗셈을 RTL에 넣지 않고, threshold comparator와 integer sum/count로 amplitude evidence를 만든다. 따라서 DSP multiplier나 divider 없이 class membrane 자극으로 fold할 수 있다.

주요 RTL 파일:

```text
rtl/core/ram_peak_accumulator.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `BANK_SIZE` | 32개 amplitude threshold |
| `BANK_BASE` | 64, 첫 threshold |
| `BANK_STEP` | 32, threshold 간격 |
| `RAM_POST_HOLD` | 80 sample, beat 이후 추가 관찰 구간 |

### 5.7 Ectopic pair neuron

Ectopic pair neuron은 RR interval 하나가 짧거나 길다는 사실만으로 바로 class evidence를 만들지 않는다. 기준 RR보다 빠른 beat와 늦은 beat가 교대로 나타나는 early/late pair를 본다.

목표는 다음과 같다.

```text
정상 rhythm 기준보다 너무 빠른 beat가 있었는가?
그 다음에 보상하듯 늦은 beat가 따라왔는가?
또는 반대로 late 이후 early가 나타났는가?
```

Ectopic pair neuron은 천천히 움직이는 reference RR을 유지한다. 새 RR이 들어오면 이 reference와 비교해서 early, late, none 중 하나로 분류한다.

```text
current_rr < rr_ref - threshold -> early_rr_spike
current_rr > rr_ref + threshold -> late_rr_spike
early 다음 late 또는 late 다음 early -> ectopic_pair_spike
```

즉 ECP는 early 하나만 보고 바로 질병 evidence라고 하지 않는다. early와 late가 교대로 나타나는 쌍을 볼 때 ectopic pair neuron이 발화한다. 이 때문에 단일 outlier나 일시적 artifact보다 “조기 박동 + 보상성 지연”처럼 보이는 rhythm pattern에 더 민감하다.

해석:

- `early_rr_spike`: 기준 RR보다 유의미하게 짧은 RR
- `late_rr_spike`: 기준 RR보다 유의미하게 긴 RR
- `ectopic_pair_spike`: early/late가 번갈아 나타난 ectopic-like pair
- 이 발화는 ARR-like rhythm evidence로 쓰인다.

주요 RTL 파일:

```text
rtl/core/ectopic_pair_neuron.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `ECTOPIC_RR_TH` | 120 sample, early/late 판정 threshold |
| `ECTOPIC_REF_SHIFT` | 4, reference RR update 속도 |

### 5.8 QRS MAF neuron

QRS MAF는 QRS Morphology Abnormality Feature이다. 단일 feature 하나가 아니라 QRS 주변 window에서 width, complexity, energy, pre-QRS bump를 함께 보는 morphology analyzer에 가깝다.

목표는 다음과 같다.

```text
QRS가 너무 넓은가?
QRS 주변 기울기 변화가 복잡한가?
QRS 주변 energy가 평소와 다르게 튀는가?
QRS 직전에 이상한 bump가 있는가?
```

동작은 beat spike를 기준으로 pre-window와 post-window를 잡는 방식이다.

```text
beat_spike 발생 전 PRE_WIN sample:
    strong_event, dscr_sign_flip, energy를 shift register로 저장

beat_spike 발생 후 POST_WIN sample:
    strong_event, dscr_sign_flip, energy를 계속 누적

window 종료:
    QRS width, complexity count, energy code, pre-QRS bump 여부 계산
```

| 세부 feature | 보는 현상 |
|---|---|
| QRS width | QRS activity가 너무 넓게 지속되는가 |
| QRS complexity | QRS window 안의 slope sign flip이 많은가 |
| QRS energy | baseline 대비 energy가 평소 reference에서 벗어나는가 |
| Pre-QRS bump | beat 직전 window에 이상 activity가 있는가 |

QRS width neuron은 QRS window 안에서 첫 activity 위치와 마지막 activity 위치를 잡고, 그 span이 threshold를 넘는지 본다. QRS complexity neuron은 window 안의 `dscr_sign_flip_spike` 수를 세고, sign flip이 많으면 복잡한 morphology로 본다. QRS energy neuron은 baseline 대비 energy가 평소 reference에서 벗어나는지 확인한다. Pre-QRS bump neuron은 beat 직전 window에 이미 strong event나 energy가 많았는지를 본다.

해석:

- `qrs_maf_valid_spike`: QRS morphology 측정 window가 끝났다는 발화
- `qrs_width_abn_spike`: QRS 폭이 넓거나 평소보다 달라졌다는 발화
- `qrs_complex_abn_spike`: QRS 주변 slope sign flip이 많다는 발화
- `qrs_energy_abn_spike`: QRS energy가 평소 reference에서 벗어났다는 발화
- `pre_qrs_bump_spike`: QRS 직전에 이상 event가 있었다는 발화

이 feature는 rhythm evidence만으로는 구분이 어려운 case에서 morphology evidence를 제공한다.

주요 RTL 파일:

```text
rtl/core/qrs_maf_neuron.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `QRS_MAF_PRE_WIN` | 120 sample, beat 이전 관찰 window |
| `QRS_MAF_WIN` | 100 sample, beat 이후 관찰 window |
| `QRS_MAF_WIDTH_TH` | 120 sample, wide QRS 기준 |
| `QRS_MAF_WIDTH_DEV_TH` | 40 sample, width deviation 기준 |
| `QRS_MAF_COMPLEX_TH` | 6, complexity count 기준 |
| `QRS_MAF_ENERGY_DEV_TH` | 8, energy deviation 기준 |

### 5.9 RBBB-like QRS delay bank

RBBB QRS delay bank는 임상적 RBBB 진단 block이 아니다. RTL 관점에서는 “wide QRS + terminal activity”가 반복되는지를 보는 conduction-delay proxy evidence block이다.

목표는 다음과 같다.

```text
QRS가 넓게 지속되는가?
QRS 후반부 terminal 구간에도 activity가 남는가?
이런 beat가 60초 안에서 반복되는가?
```

먼저 QRS activity onset neuron이 있다.

```text
strong_event 또는 slope_valid가 발생하고
직전 clock에는 activity가 없었고
현재 QRS 관찰 window가 닫혀 있으면
qrs_onset_spike 발화
```

onset 이후 QRS observation window가 열린다.

```text
qrs_age가 0부터 증가
activity가 계속 있는지 관찰
activity gap이 길어지거나 MAX_QRS_OBS_WIN에 도달하면 QRS window 종료
```

그 안에서 delay bank가 작동한다.

```text
80 ms, 90 ms, 100 ms, ..., 160 ms 지점에 activity가 있었는지 기록
가장 늦게 activity가 남은 지점을 last_matched_width로 본다.
last_matched_width >= WIDE_WIDTH_TH이면 wide_qrs_spike
```

terminal delay neuron은 QRS 후반부를 본다.

```text
TERMINAL_START부터 TERMINAL_END 사이 activity 개수를 센다.
terminal activity count >= TERMINAL_COUNT_TH이면 terminal_delay_spike

wide_qrs_spike와 terminal_delay_spike가 동시에 만족되면
rbbb_like_beat_spike 발화
```

마지막으로 segment-level 반복성을 본다.

```text
60초 동안 rbbb_like_beat_count가 repeat threshold 이상이면
rbbb_segment_spike 발화
```

해석:

- `wide_qrs_spike`: QRS width가 넓다는 morphology 발화
- `terminal_delay_spike`: QRS 후반부 activity가 남는다는 발화
- `rbbb_like_beat_spike`: wide + terminal delay가 같이 나타난 beat
- `rbbb_segment_spike`: 이런 beat가 60초 안에서 반복되었다는 segment evidence

이 evidence는 NSR을 억제하거나 ARR/CHF/AFF 쪽 morphology evidence를 보강하는 방향으로 class score membrane에 반영될 수 있다.

주요 RTL 파일:

```text
rtl/core/rbbb_qrs_delay_bank.v
```

주요 파라미터:

| 항목 | 현재 값/의미 |
|---|---|
| `RBBB_QRS_MAX_OBS_WIN` | 200 sample, QRS observation window 상한 |
| `RBBB_QRS_TERMINAL_START` | 90 sample, terminal activity 시작 |
| `RBBB_QRS_TERMINAL_END` | 170 sample, terminal activity 종료 |
| `RBBB_QRS_WIDE_TH` | 120 sample, wide QRS 기준 |
| `RBBB_QRS_TERMINAL_TH` | 4, terminal activity count 기준 |
| `RBBB_QRS_REPEAT_TH` | 5, segment-level 반복 기준 |

### 5.10 Class score neurons와 60초 WTA

위 feature neuron들이 만든 spike와 count는 `class_score_neurons.v`로 들어간다. 이 block은 NSR/CHF/ARR/AFF class membrane 네 개를 유지하고, 각 feature evidence를 fixed signed weight로 더하거나 뺀다.

Python 관점에서는 다음처럼 보일 수 있다.

```text
score[class] += feature_count * coefficient[class]
score[class] += bias[class]
```

하지만 RTL에서는 floating-point 곱셈을 수행하지 않는다. coefficient와 bias는 integer signed weight와 folded bias로 흡수되어 있고, feature spike/count가 들어올 때 class membrane에 정수 add/subtract를 수행한다.

```text
feature spike/count 발생:
    class_mem[NSR] += W_feature_to_NSR
    class_mem[CHF] += W_feature_to_CHF
    class_mem[ARR] += W_feature_to_ARR
    class_mem[AFF] += W_feature_to_AFF

60초 segment_done:
    pred_class = WTA(class_mem)
```

weight가 양수이면 해당 class membrane에 흥분성 자극을 주는 것이고, 음수이면 억제성 자극을 주는 것이다. 이 때문에 본 설계는 “feature vector + software classifier”가 아니라 “feature spike + class membrane + WTA” 구조로 설명할 수 있다.

예를 들면 다음과 같이 해석할 수 있다.

```text
PNN mismatch와 RDM variability가 반복됨
-> irregular rhythm evidence 발화
-> ARR/AFF membrane에 흥분성 자극 가능
-> NSR membrane에는 억제성 자극 가능

QRS MAF 또는 RBBB-like delay가 반복됨
-> morphology/conduction-delay proxy evidence 발화
-> NSR을 억제하거나 ARR/CHF/AFF membrane을 보강
```

60초 segment가 끝나면 class membrane 네 개를 WTA로 비교한다. Tie-break 순서는 RTL과 Python golden이 동일해야 하므로, 최종 검증에서는 `final_pred`뿐 아니라 `final_mem`까지 비교했다.

## 6. Final Membrane Readout

Final Membrane Readout은 30개의 60초 snapshot에서 나온 evidence를 class별 membrane에 누적한다. 단순 majority vote와 달리, snapshot WTA에서 드러난 class뿐 아니라 subthreshold evidence와 guard/rescue 조건을 반영한다.

최종 locked candidate:

```text
structural_guarded_silent_aff_1008710
```

이 candidate는 train/validation만 사용한 structural-grid search 후 확정되었고, final_test 결과를 보고 파라미터를 수정하지 않았다.

## 7. Fully Blind Strict Record-wise 프로토콜

최종 protocol의 핵심은 record leakage를 막는 것이다. Split 단위는 `source_record_id`이며, 동일 source record에서 나온 30분 청크가 train/validation/final_test에 동시에 들어가지 않도록 구성한다.

| 항목 | 값 |
|---|---|
| Split 단위 | `source_record_id` |
| 최종 모델 | `structural_guarded_silent_aff_1008710` |
| final_test 모델 선택 사용 여부 | 사용하지 않음 |
| final_test 파라미터 탐색 사용 여부 | 사용하지 않음 |
| final_test 외부 논의 문맥 사용 여부 | 사용하지 않음 |
| final_test 평가 횟수 | 1 |
| Validation 역할 | 모델 선택 전용 |

Validation 100%는 최종 일반화 성능이 아니라 model-selection 성능이다. 최종 성능 주장은 locked final_test 결과만 사용한다.

## 8. 결과

### 8.1 Strict Record-wise 결과

| Split | 정답 / 전체 | 정확도 |
|---|---:|---:|
| Train | 61 / 68 | 89.71% |
| Validation | 32 / 32 | 100.00% |
| Final test 30분 청크 | 29 / 36 | 80.56% |
| Final test record-majority | 16 / 19 | 84.21% |

### 8.2 XSim

| 검증 항목 | 결과 |
|---|---:|
| final_test case 수 | 36 |
| final_pred mismatch | 0 |
| final_mem mismatch | 0 |

### 8.3 Vivado / IP / Board

| 항목 | 결과 |
|---|---|
| Pure RTL 자원 | LUT/FF/BRAM/DSP 9719/5038/0/0 |
| Pure RTL timing | WNS 8.184 ns |
| Vivado 추정 total power | 0.099 W |
| AXI/IP-XACT | accelerator와 sample feeder packaged |
| MicroBlaze full replay system | bitstream/XSA/ELF 생성, timing met |
| Board replay | NSR/CHF/ARR/AFF 각 1개 30분 case, final_pred/final_mem exact 4/4 |

## 9. 하드웨어 구현과 IP Packaging

Accelerator는 AXI4-Lite control/status와 AXI4-Stream sample input을 갖는 재사용 가능한 RTL/IP block으로 구현했다. MicroBlaze board replay path에서는 작은 MMIO-to-AXIS sample feeder를 사용하여 16-bit sample data와 TLAST timing을 deterministic하게 제어한다.

최종 hardware artifact는 다음과 같다.

| 산출물 | 경로 |
|---|---|
| Locked parameter | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |
| RTL parameter include | `rtl/strict_recordwise_locked_params.vh` |
| Accelerator IP-XACT | `ip_repo/snn_ecg_axi_accelerator/component.xml` |
| Feeder IP-XACT | `ip_repo/axi_lite_axis_sample_feeder/component.xml` |
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| MicroBlaze ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |

## 10. 논의

본 프로젝트의 기여는 analog physical measurement가 아니라, AFE+ADC XMODEL과 digital accelerator IP를 연결한 biomedical mixed-signal-to-digital FPGA prototype이다. Multiply-heavy neural network 대신 event/spike evidence, counter/comparator, signed membrane accumulation, WTA를 사용해 low-resource RTL 구조를 구성했다.

Board replay는 class-wise 대표 4개 30분 record에서 bit-exact 결과를 확인했다. 전체 final_test 36개 case의 board batch replay와 board-level current/power measurement는 남은 확장 검증이다.

## 11. 결론

본 repo의 최종 결과는 locked strict record-wise protocol과 hardware validation이 연결된 SNN-inspired ECG 4-class accelerator IP prototype이다. 최종 모델은 train/validation으로 lock되고 final_test를 1회 평가했으며, RTL/XSim/Vivado/IP/Vitis evidence가 같은 locked model 기준으로 정리되었다.

## 부록. 최종 산출물 목록

- 최종 모델 source of truth: `configs/final_submission_locked_model.json`
- 최종 metric: `reports/final/final_metrics.json`
- Strict record-wise 결과: `reports/final/strict_recordwise_final_result.md`
- Hardware validation: `reports/final/hardware_validation_result.md`
- Board replay 결과: `reports/final/board_replay_result.md`
- Figure: `reports/final/figures/`
