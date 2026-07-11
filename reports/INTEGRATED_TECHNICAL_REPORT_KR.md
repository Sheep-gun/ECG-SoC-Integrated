# 장시간 ECG 4-Class 분류를 위한 다중 시간축 SNN-Inspired Streaming RTL Accelerator IP

# 초록

본 연구는 장시간 심전도(electrocardiogram, ECG)에서 짧은 구간의 박동·파형 정보와 장기 지속성을 함께 반영하는 다중 시간축 분류 구조를 제안하고, 이를 1 kSPS signed 12-bit streaming RTL accelerator IP로 구현·검증하였다. 한 표본값은 1 ms마다 들어오며, 인접 표본값의 변화가 사건 신호(event)로 변환된다. 반복되는 강한 변화는 막전위형 상태에 누적되어 한 번의 박동을 만들고, 박동 간격의 규칙성·변동성과 박동 주변의 기울기 전환·진폭·폭·에너지·말단 활동도가 정수형 상태로 압축된다. 이 정보는 60,000표본의 60초 Snapshot에서 국소 class 상태를 형성하고, 30개 Snapshot의 class winner와 집계 특징이 30분 Final Membrane에 누적된 뒤 승자독식 방식으로 NSR·CHF·ARR·AFF 중 하나를 출력한다. MATLAB nominal AFE+ADC, SystemVerilog XMODEL stress, signed-stream SHA256, Python integer reference, RTL/XSim, Vivado, AXI/IP-XACT, Vitis/MicroBlaze와 FPGA replay를 하나의 evidence chain으로 연결하였다. Strict source-record-wise split에서 locked final-test chunk 결과는 29/36=80.56%, record-majority는 16/19=84.21%였다. Pure RTL은 LUT 9,719, FF 5,038, BRAM 0, DSP 0으로 구현되었고 FPGA final_pred/final_mem은 XSim 기준과 각각 36/36 일치하였다. 전체 1,800,000표본 raw window를 저장하지 않는 구조이지만, database–class confounding, physical AFE/ADC·임상 검증 부재와 pending accelerator benchmark가 남는다. 따라서 본 결과는 임상 진단의 증명이 아니라 장시간 네 class 분류를 이해 가능한 정수형 사건/상태 구조와 재현 가능한 RTL/IP/FPGA artifact로 완결한 반도체 IP 공학 결과다.

# 핵심어

심전도, 장시간 모니터링, SNN-inspired architecture, 사건 기반 처리, Snapshot Readout, Final Membrane, streaming RTL, FPGA accelerator

# 1. 서론

## 1.1 연구 배경과 문제 정의

ECG는 심장의 전기적 활동이 시간에 따라 만든 전압 파형이다. 짧은 ECG 조각에서는 한두 번의 박동 형태를 자세히 볼 수 있지만, 장시간 기록에서는 박동 간격의 반복성, 불규칙성이 나타나는 빈도, 특정 파형 특징의 지속 여부가 함께 중요하다. Ambulatory ECG는 증상 빈도와 관찰 목적에 따라 24/48시간 Holter 또는 더 긴 감시 방식을 사용할 수 있다[2]. 이는 한 시점의 파형만으로 장시간 상태를 대표하기 어렵다는 공학적 동기를 제공한다.

대표적인 소비자용 단일유도 ECG 앱의 FDA 문서 사례는 sinus rhythm과 atrial fibrillation 중심의 rhythm-screening 범위를 설명한다[1]. 본 연구는 그 제품과 정확도를 비교하지 않는다. 공개 데이터에서 NSR(normal sinus rhythm), CHF-labelled, ARR(arrhythmia-labelled), AFF(atrial-fibrillation-labelled) 네 범주를 다루는 장시간 공학 문제를 정의하고, 국소 리듬·파형 증거를 30분 동안 누적하는 투명한 하드웨어 구조를 설계한다. NSR은 질병이 아니며 ARR은 넓은 label이고 CHF 역시 해당 source DB의 label이다. 따라서 출력은 네 질환의 확진이 아니라 현재 공개 데이터 구성의 네 public-dataset class다 [CLM-001].

문제의 핵심은 1,800,000개 표본값을 모두 저장한 뒤 소프트웨어 batch classifier를 실행하는 것이 아니다. 입력을 받는 즉시 작은 정수형 상태를 갱신하면서도 다음 세 시간척도를 잃지 않아야 한다.

- **표본값 시간척도:** 1 ms마다 파형 변화와 detector 상태를 갱신한다.
- **박동 시간척도:** 검출된 박동 사이 간격과 박동 중심 파형 구간을 평가한다.
- **구간·장시간 시간척도:** 60초 증거를 Snapshot으로 확정하고 30개 Snapshot을 Final Membrane에 누적한다.

![그림 1. 장시간 ECG에서 서로 다른 시간척도의 증거](../figures/final/FIG-01_long_window_motivation.svg)

*그림 1. 표본값·박동·60초·30분으로 이어지는 문제의 시간 계층. Holter-oriented는 설계 방향이며 임상 인증을 뜻하지 않는다. [근거: CLM-001, CLM-003]*

## 1.2 연구 목표와 주요 기여

연구 목표는 공개 ECG를 공통 signed 12-bit stream으로 변환하고, 리듬과 파형 형태를 사건 신호와 지속 상태로 압축하여 30분 class를 출력하는 RTL IP를 만드는 것이다. 속도 자체가 주 기여는 아니다. 핵심은 장시간 네 class 분류 구조를 설명 가능한 fixed-width 회로로 구현하고 model-based analog intent부터 FPGA output까지 같은 신호·상태를 추적하는 데 있다.

주요 기여는 다음 여섯 가지다.

1. NSR·CHF·ARR·AFF의 장시간 four-class engineering target을 정의하였다.
2. 60초 Snapshot과 30분 Final Membrane을 결합해 국소 증거와 장기 지속성을 분리·재결합하였다.
3. 인접 표본값 변화, 막전위형 박동 검출, RR 리듬, 파형 형태를 정수 counter·comparator·accumulator로 구현하였다.
4. 전체 30분 raw window 없이 고정 크기 persistent state를 갱신하는 streaming datapath를 구현하였다 [CLM-023].
5. MATLAB→XMODEL→signed stream→RTL/IP→FPGA로 이어지는 기능 등가성 사슬을 구축하였다.
6. Fixed commit, artifact hash, dataset manifest, ownership/claim registry와 checker로 수치와 해석 경계를 통제하였다.

| 목표 | 구현·검증 결과 | 해석 경계 |
|---|---|---|
| 장시간 네 class 분류 | 60초 Snapshot×30, final 29/36 | public-dataset engineering result |
| 사건/상태형 RTL | fixed-width counter·비교·signed membrane | trained deep SNN 아님 |
| 전체 window 비저장 | sample-by-sample persistent state | measured memory saving 아님 |
| Mixed-signal handoff | SHA256와 canonical pred/mem 36/36 | model-based analog |
| FPGA IP | Vivado·IP-XACT·MicroBlaze·board replay | clinical device/ASIC 아님 |
| Accelerator benefit | `PENDING_EXTERNAL_BENCHMARK_IMPORT` | speed·power·energy 미확정 |

*표 1. 연구 목표와 달성 결과. 각 행은 서로 다른 evidence scope를 갖는다. [근거: CLM-003, CLM-004, CLM-008~CLM-013, CLM-018, CLM-023]*

표 1에서 구조·분류·통합·FPGA 구현은 artifact로 확인되지만 accelerator benchmark는 pending이다. 이 구분은 “FPGA에 올라갔다”는 사실을 곧바로 고속·저전력 우월성으로 바꾸지 않기 위한 것이다.

# 2. 전체 시스템과 평가 방법

## 2.1 신호 처리 및 구현 흐름

전체 신호 흐름은 `public ECG → MATLAB nominal AFE+ADC → SystemVerilog XMODEL → 1 kSPS signed 12-bit stream → 사건/상태형 digital core → RTL/IP/FPGA replay`다. MATLAB은 nominal filter·gain·ADC 범위와 reference vector를 제공하고, XMODEL은 PLI·offset·mismatch·op-amp·ADC non-ideal과 long signed stream을 검토한다. Digital core는 그 stream을 받아 Snapshot과 Final Membrane을 계산한다.

![그림 2. 전체 시스템 흐름](../figures/final/FIG-02_complete_system_flow.svg)

*그림 2. 공개 ECG에서 model-based AFE/ADC와 digital IP를 거쳐 FPGA replay로 이어지는 흐름. Analog layer는 physical measurement가 아니다.*

Handoff의 canonical interface는 표 2와 같다. `sample_valid && sample_ready`가 참인 clock에서만 한 표본값이 accepted sample로 처리된다. XSim integration에서는 accepted sample 사이의 canonical `sample_gap_cycles=2`를 사용한다. 이 cadence는 1 kSPS input convention과 다른 개념이며 accelerator throughput 수치도 아니다.

| 항목 | Canonical contract | 의미 |
|---|---:|---|
| 입력 표현 | signed 12-bit two’s-complement | AFE/ADC model과 digital core의 code 규약 |
| 입력 표본률 | 1,000 samples/s | 한 표본값 간격 1 ms |
| Snapshot | 60,000 accepted samples | 60초 국소 상태 확정 |
| Final decision | 30 Snapshots | 1,800,000 samples=30분 |
| XSim cadence | `sample_gap_cycles=2` | board-facing canonical 검증 조건 |
| 출력 | `final_pred`+4개 `final_mem` | class winner와 내부 signed final states |

*표 2. 전체 interface contract. [근거: CLM-002, CLM-003, CLM-013; `components/digital_accelerator/reports/final/digital_input_contract.md`]*

구현 ownership은 서민우(MATLAB nominal/vector), 이수환(XMODEL/stress/integration), 양건(digital architecture/evaluation/RTL/IP/FPGA/총괄)으로 분리한다. Handoff hash와 output comparison이 세 component를 연결하지만 협업이 각 구현 책임을 이전하지는 않는다.

## 2.2 데이터셋과 평가 프로토콜

네 class는 서로 다른 PhysioNet database에서 왔다. Raw waveform은 public Git에 번들하지 않고 version 1.0.0, DOI, source rate, 사용 record와 expected SHA256를 manifest로 고정한다. Fetch/verify 도구는 저장소 밖에 원본을 복원하며 ODC-By 1.0 attribution과 database-specific citation을 따른다[3]–[8].

| Class | Source/version | Source rate | DOI | Final-test record support |
|---|---|---:|---|---:|
| NSR | nsrdb 1.0.0 | 128 Hz | 10.13026/C2NK5R | 5 |
| CHF | chfdb 1.0.0 | 250 Hz | 10.13026/C29G60 | 4 |
| ARR | mitdb 1.0.0 | 360 Hz | 10.13026/C2F305 | 9 |
| AFF | afdb 1.0.0 | 250 Hz | 10.13026/C2MW2D | 1 |

*표 3. Dataset source와 final-test record support. [근거: EXT-003~EXT-008; `datasets/dataset_manifest.yaml`; `datasets/DATASET_LICENSES.md`]*

각 source는 공통 1 kSPS signed 12-bit convention으로 변환되지만 이것이 lead·장비·population·noise 차이를 제거했다는 뜻은 아니다. Class와 DB가 일대일로 결합되므로 database–class confounding이 남는다 [CLM-017]. 고정 버전 raw waveform을 번들하지 않는다. Dataset manifest·license·expected SHA와 fetch/verify 도구로 저장소 밖에 복원하고, 보고서에 쓰는 locked derived evidence만 보존한다.

Split unit은 `source_record_id`다. 한 physical record에서 생성된 모든 30분 chunk는 train, validation, final test 가운데 하나에만 속한다. 이 방법은 직접 record leakage를 막지만 DB identity와 class identity의 결합은 해소하지 않는다 [CLM-016].

| Partition | Class별 chunk | 전체 | 역할 |
|---|---:|---:|---|
| Train | 17×4 | 68 | fitting 확인 |
| Validation | 8×4 | 32 | Final Membrane model selection |
| Locked final test | 9×4 | 36 | lock 후 1회 평가 |
| Final source records | 5/4/9/1 | 19 | record-majority 집계 단위 |

*표 4. Strict source-record-wise split. [근거: CLM-007, CLM-016; `components/digital_accelerator/configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json`]*

Locked model `structural_guarded_silent_aff_1008710`은 train/validation으로 선택한 뒤 threshold·weight·structural logic을 동결했다. Final test는 selection이나 parameter search에 사용하지 않았고 평가 횟수는 1, `test_used_for_selection=false`다 [CLM-007]. Accuracy, macro F1, balanced accuracy와 class recall을 사용하며 record-majority는 같은 final partition의 chunk를 record별 다수결로 합친 값이지 독립 test가 아니다.

# 3. 제안 SNN-Inspired 디지털 아키텍처

## 3.1 핵심 개념과 다중 시간축 처리

이 절은 RTL module 이름보다 먼저 회로가 다루는 기본 개념을 정의한다.

**표본값(sample).** 한 표본값은 한 시점의 digitized ECG 전압 code다. 1 kSPS에서는 1 ms마다 한 값이 들어온다. 60초에는 60,000개, 30분에는 1,800,000개 표본값이 있다.

**파형 변화 사건 신호(event).** 현재 표본값에서 직전 표본값을 빼면 파형이 위로 움직였는지 아래로 움직였는지와 변화 크기를 알 수 있다. 사건 신호는 특정 조건이 발생했음을 한 clock 동안 알리는 짧은 digital pulse이며 analog waveform 자체를 저장한 것이 아니다.

**막전위형 상태(membrane state).** 여러 사건을 시간에 따라 더하는 register형 accumulator다. 지지 사건이 오면 증가하고, 필요하면 시간이 지나며 누설(leak)되어 줄어들고, 문턱값(threshold)을 넘으면 spike나 decision을 만든다. 누설은 오래된 단발 사건이 영원히 남지 않게 하고 문턱값은 누적 정도를 discrete event로 바꾼다. 본 locked QRS detector의 generic 구조에는 leak 연산이 있지만 현재 top 설정의 QRS leak 값은 0이다. 따라서 “누설 가능한 구조”와 “이번 locked configuration에서 실제 감소하는가”를 구분한다.

**불응기(refractory, refractory period).** 한 박동을 검출한 직후 일정 accepted-sample 동안 detector를 잠시 막는다. QRS 파형은 여러 인접 표본에서 큰 변화를 만들 수 있으므로 불응기가 없으면 하나의 QRS를 여러 박동으로 셀 수 있다.

**박동과 RR interval.** 박동(beat)은 내부 detector가 낸 한 clock의 `beat_spike`다. RR interval은 연속된 두 `beat_spike` 사이 accepted-sample tick 수다. 실제 R-peak annotation을 직접 읽는 것이 아니라 본 detector가 만든 event 사이 시간이다.

**Snapshot.** Snapshot은 이미지가 아니다. 60,000표본 동안 발생한 박동·리듬·파형 사건과 class 상태를 확정한 60초 요약이다. 다음 60초가 시작되면 local detector/counter는 reset되지만 Snapshot 결과는 Final Membrane으로 전달된다.

**Final Membrane.** 네 class 각각에 대응하는 signed long-window 상태다. 30개 Snapshot의 winner count와 rhythm/morphology aggregate를 모아 positive·negative class evidence를 적용한 뒤 최종 WTA에 사용한다.

**왜 SNN-inspired인가.** Dense 방식은 모든 파형값 또는 큰 feature vector를 보존해 한꺼번에 처리할 수 있다. 본 구조는 의미 있는 변화가 발생할 때 사건 pulse를 만들고, 그 pulse를 persistent state에 누적하며, membrane·threshold·spike·WTA로 시간 정보를 decision으로 바꾼다. 즉 event-driven evidence, membrane-like state, threshold crossing, temporal accumulation과 winner-take-all을 fixed-point RTL에 차용했다. 그러나 trained deep SNN, STDP, online learning, biophysical neuron simulation이나 biological equivalence는 아니다.

![그림 3. 다중 시간축 구조](../figures/final/FIG-04_multitimescale_architecture.svg)

*그림 3. 1 ms 표본값, 박동, 60초 Snapshot, 30분 Final Membrane의 세 단계 상태 이동. [근거: CLM-003, CLM-023]*

![그림 4. 디지털 아키텍처](../figures/final/FIG-12_detailed_digital_architecture.svg)

*그림 4. 독자 개념을 중심으로 정리한 digital architecture. Module 이름은 구현 확인용 보조 표기이며 literal netlist를 대체하지 않는다.*

이후 절에서 반복해서 사용할 비임상 설명 예는 다음과 같다. ECG code가 여러 표본에 걸쳐 빠르게 상승하면 변화 event가 연속 발생한다. 강한 event가 QRS membrane의 문턱을 넘으면 한 박동이 만들어지고, 이전 박동 이후 tick 수가 RR interval이 된다. 리듬 경로는 interval의 반복성과 변화량, early–late pattern을 보고, 파형 경로는 기울기 전환·peak code·width·energy·terminal activity를 본다. 60초 동안 이 값들이 class state에 누적되고 30개 Snapshot 뒤 WTA가 final class를 선택한다. 이 예는 state flow를 설명할 뿐 실제 환자의 진단 예가 아니다.

## 3.2 박동 및 리듬 정보 추출

![그림 5. 박동·리듬 경로](../figures/final/FIG-13_beat_rhythm_path.svg)

*그림 5. 인접 표본값 차이에서 beat, RR, PNN/RDM/early–late evidence로 이어지는 state transition. [근거: fixed digital RTL `c6b80de...`]*

**1) 인접 표본값의 변화.** ECG의 절대 code는 source scale, baseline과 lead의 영향을 받을 수 있다. 반면 인접 표본값 차이는 지금 이 순간 파형이 얼마나 빠르게 상승·하강하는지 직접 표현한다. 그렇다고 amplitude invariance가 증명되는 것은 아니다. 회로는 첫 valid 표본값을 `prev_sample`에 저장하고 event를 내지 않는다. 두 번째부터 현재 signed code를 13 bit로 sign-extension한 뒤 이전 code와 뺀다.

```text
delta_next     = signed(current_sample) - signed(previous_sample)
abs_delta_next = |delta_next|
direction      = up if delta_next > positive_slope_condition
                 down if delta_next < negative_slope_condition
strong_event   = abs_delta_next > active_event_condition
previous_sample_next = current_sample
```

Old state는 직전 clock의 `prev_sample`, 계산 상태는 `delta_calc/abs_delta_calc`, commit은 accepted sample의 rising edge다. `up_event`, `down_event`, `strong_event`, `slope_valid`는 기본적으로 한 clock pulse로 0에 돌아갔다가 조건을 만족한 표본에서만 1이 된다. Segment 시작 시 adaptive histogram과 12개 threshold-bank counter를 지운다. Locked top은 adaptive bank mode를 켜므로 초기 calibration 표본에서 각 변화 크기 후보를 넘은 횟수를 세고, 목표 event density를 만족하는 bank threshold를 선택한 뒤 `adaptive_ready`를 올린다. 선택 전에는 fixed event threshold를 사용한다. 구현 module은 `ecg_event_encoder_adaptive`이며 출력은 QRS detector, DSCR, QRS MAF와 RBBB-like path로 분기된다.

**2) 여러 변화 event를 한 박동으로 묶기.** 한 개의 큰 변화만으로 박동을 확정하면 noise에 민감하고, 반대로 QRS를 이루는 여러 큰 변화를 각각 beat로 세면 중복 count가 생긴다. 그래서 detector는 strong event를 막전위형 상태에 더한다. 조합 logic은 old `qrs_mem`에서 leak를 먼저 적용하고, 현재 strong event의 weight를 더한 `mem_after_event`를 만든 다음 같은 accepted sample에서 threshold를 비교한다. Threshold 미만이면 이 값을 next membrane으로 commit한다. Threshold 이상이면 next `beat_spike=1`, membrane=0, refractory counter=locked duration으로 commit한다.

```text
if refractory_old != 0:
    membrane_next  = 0
    refractory_next = refractory_old - 1
else:
    after_leak  = max(membrane_old - configured_leak, 0)
    after_event = after_leak + event_weight if strong_event else after_leak
    if after_event >= beat_threshold:
        beat_spike_next = 1
        membrane_next = 0
        refractory_next = configured_refractory
    else:
        membrane_next = after_event
```

`beat_spike`는 다음 clock에 register되어 한 cycle만 유지된다. 불응기 동안 membrane을 0으로 유지하고 counter를 accepted sample마다 감소시키므로 같은 QRS의 후속 변화가 새 박동으로 다시 누적되지 않는다. Generic module은 leak를 지원하지만 locked top의 `QRS_LEAK`는 0임을 앞서 구분하였다. 구현 module은 `qrs_lif_detector`다.

**3) RR interval 확정.** 첫 `beat_spike`는 token을 활성화하고 `token_age`를 0으로 만든다. 이후 accepted sample마다 `rhythm_tick`이 들어오면 age가 saturation 방식으로 1씩 증가한다. 다음 beat가 오면 현재 tick을 포함한 `age_eval`을 `rr_interval`과 evaluation register에 복사하고 token age를 다시 0으로 만든다. 첫 beat에는 이전 interval이 없으므로 RR output을 평가하지 않는다. 이 순서 때문에 RR은 임의 wall-clock 시간이 아니라 accepted-sample count다.

**4) PNN 고정 rhythm hypothesis.** `pnn_rhythm_predictor`의 46개 hypothesis center는 일정 간격으로 배치된 가능한 RR 중심값이다. 새 RR이 확정되면 한 clock에 모두 비교하는 대신 `eval_idx`가 center를 하나씩 순회한다. 각 center와 RR의 absolute distance를 구하고 기존 best error보다 작을 때만 best ID를 교체한다. 동일 거리에서는 먼저 본 낮은 ID가 유지된다. 마지막 center 평가 후 winner ID와 error를 commit한다.

PNN의 “예측”은 현재 RR winner를 다음 RR의 predictor ID로 보관하는 방식이다. 다음 RR이 들어오면 scan과 별도로 이전 predictor center와의 distance를 계산한다. Locked prediction window 안이면 `pnn_match_spike`, 밖이면 `pnn_mismatch_spike`를 한 cycle 발생시킨다. 따라서 PNN이 묻는 질문은 “다음 박동 간격이 이전에 선택한 recurring interval pattern을 따르는가?”다. 이는 general probabilistic neural-network classifier가 아니라 fixed RR-hypothesis mechanism이다.

**5) RDM 연속 interval 변화량.** PNN이 pattern consistency를 본다면 RDM은 바로 앞 두 interval의 차이가 얼마나 큰지 본다. 첫 valid RR은 `prev_rr`만 초기화한다. 다음 RR부터 `abs(current_rr-prev_rr)`를 계산하고 15개 threshold level을 누적적으로 표시하는 thermometer-style `rdm_level_spike[14:0]`와 가장 높은 level을 나타내는 4-bit code를 출력한다. 같은 clock에 `prev_rr`를 현재 RR로 교체하므로 다음 비교의 기준이 된다. 즉 PNN은 “예측한 중심을 따르는가”, RDM은 “연속 RR끼리 얼마나 달라졌는가”라는 서로 다른 정보를 Snapshot에 제공한다. 구현 module은 `rdm_variability_neuron`이다.

**6) Early–late pair.** 첫 RR은 adaptive reference `rr_ref`를 초기화한다. 이후 RR이 reference보다 충분히 짧으면 early, 충분히 길면 late pattern으로 표시하고, 직전 non-normal pattern을 `prev_pattern`에 보관한다. Current pattern과 previous pattern이 모두 유효하고 서로 다르면 early→late 또는 late→early 조합이므로 `ectopic_pair_spike`를 발생시킨다. 매 interval마다 reference는 `|RR-ref|`를 right shift한 작은 step만큼 현재 RR 방향으로 이동한다. Normal 범위 RR은 pair state를 바꾸지 않고, segment start에서 reference와 pattern을 지운다. 구현 module은 `ectopic_pair_neuron`이며 pair spike는 Snapshot morphology/rhythm class contribution과 long-window counter에 쓰인다.

| 관찰 대상 | 필요한 이유 | 구체적인 하드웨어 처리 | 생성 상태 | 사용 위치 | 구현 모듈 |
|---|---|---|---|---|---|
| 파형 변화 | QRS 후보와 기울기 방향 | previous sample signed subtraction, absolute magnitude, adaptive bank | up/down/strong event | QRS·DSCR·QRS MAF·delay path | `ecg_event_encoder_adaptive` |
| 박동 | 여러 변화 pulse를 한 beat로 결합 | old membrane→leak→event add→threshold, refractory countdown | `beat_spike`, QRS membrane | RR 및 beat-window trigger | `qrs_lif_detector` |
| RR pattern | 반복 interval consistency | 46 center 순차 distance scan, previous winner prediction | match/mismatch spike | Snapshot class state | `pnn_rhythm_predictor` |
| RR 변화량 | 연속 interval 변동 크기 | previous RR absolute difference, 15 threshold levels | RDM level/code | Snapshot counter와 Final aggregate | `rdm_variability_neuron` |
| Early–late 조합 | 보상성 interval pattern | adaptive reference, previous non-normal pattern retention | pair spike | morphology/rhythm contribution | `ectopic_pair_neuron` |

*표 5. Rhythm path의 실제 state mechanism. Module 이름은 마지막 열의 구현 확인 정보다.*

**통합 해석 경계.** 이 경로의 beat, RR, PNN, RDM과 ectopic-pair는 locked hardware 내부 proxy다. Clinical QRS annotation, 표준 HRV 지표, probabilistic neural network 또는 ectopic diagnosis와 동일하다고 주장하지 않는다. 이 제한은 각 block마다 반복하지 않고 이 절 전체에 적용한다.

## 3.3 파형 형태 및 진폭 정보 추출

Rhythm만으로는 같은 interval pattern 안의 파형 차이를 설명하기 어렵고, 파형 형태만으로는 장기 규칙성을 설명하기 어렵다. 따라서 beat 경로와 병렬로 기울기 방향 전환, peak code, QRS 주변 폭·복잡도·에너지와 terminal delay를 추출한다.

![그림 6. 파형 형태 경로](../figures/final/FIG-14_morphology_path.svg)

*그림 6. DSCR·RAM·QRS MAF·RBBB-like path가 finite state로 파형을 압축하는 과정. [근거: fixed digital RTL `c6b80de...`]*

**1) DSCR 기울기와 방향 전환.** `dscr_spike_counter`는 raw sample을 바로 빼지 않고 fixed-point filter state `filt_mem`을 완만하게 따라가게 한다. 현재 code를 fractional format으로 바꾸고 `filter_error=sample-filt_mem`, `filter_update=error>>>FILTER_SHIFT`, `filt_next=filt_mem+filter_update`를 계산한다. Update의 부호가 상승/하강 방향이고 absolute update를 정수 기울기 입력으로 사용한다.

Locked parameter 조합은 fast slope path 조건을 만족한다. 변화 크기가 slope condition을 넘으면 즉시 `valid_slope_spike`와 current sign을 만들고, 그렇지 않은 작은 값은 low bits의 up/down state로 남지만 다음 accepted sample의 fast-path next state는 다시 0에서 계산된다. 유효 기울기가 발생하면 `prev_slope_valid`와 `prev_slope_sign`에 방향을 commit한다. 이전 유효 방향과 현재 방향이 다를 때 sign membrane condition을 통과해 `sign_flip_spike`를 만든다. Locked sign configuration에서는 한 방향 전환이 곧 한 flip pulse가 된다.

```text
유효 기울기 부호:  +  →  +  →  -
이전 부호와 비교:  없음   동일   다름
flip 사건 신호:     0      0      1

유효 기울기 부호:  +  →  +  →  +
flip 사건 신호:     0      0      0
```

`clear=segment_start`에서 filter, up/down/sign state와 previous sign을 지운다. 60초 동안 `valid_slope_spike`와 `sign_flip_spike`가 각각 slope count와 morphology count에 누적된다.

**2) RAM peak 진폭 code.** 진폭 경로는 PNN이 예측한 다음 RR 중심 주변에서 `ram_window_open`을 만든다. Token이 active이고 predictor가 valid하며 현재 token age가 predictor center의 허용 범위 안일 때 관찰 구간이 열린다. Rising edge에서 peak code, beat-seen flag와 post-hold state를 초기화한다. Locked top에서는 input normalizer가 꺼져 있고 RAM/QRS MAF baseline 입력은 signed zero이므로, accepted sample마다 `max(adc_data-baseline,0)`의 positive amplitude를 사용한다.

Threshold bank는 amplitude가 넘은 가장 높은 bank index+1을 작은 code로 바꾼다. 각 sample code가 현재 peak code보다 크면 교체한다. RTL 이름 `r_peak_abs`는 오해하기 쉽지만 현재 구현에서 이 register는 full-resolution amplitude가 아니라 zero-extended **최대 amplitude code**를 보관한다. Window 안에서 beat가 발생하면 post-hold counter를 시작해 박동 뒤 일정 표본까지 계속 최대 code를 찾는다. Hold 종료 시 beat가 있었다면 `ram_amp_code`와 한 cycle의 `ram_amp_spike`를 출력한다. Top은 60초 동안 code sum과 valid code count를 누적한다. 파형 전체를 보관하지 않고 한 beat의 peak를 작은 정수 하나로 압축하는 구조다. 구현 module은 `ram_peak_accumulator`다.

**3) QRS MAF의 박동 전후 관찰.** `qrs_maf_neuron`은 한 줄짜리 “width/energy block”이 아니라 다음 state machine을 가진다.

- **박동 전 120표본:** `pre_strong_sr`, `pre_flip_sr`와 120개의 8-bit energy-code history를 shift한다. Strong event count, sign-flip count, energy sum을 sliding 방식으로 유지하고 strong-event time FIFO로 oldest/newest 위치를 추적한다.
- **박동 시작:** `beat_spike`에서 pre-window count/sum을 snapshot하고 100표본 post window를 연다. Pre-window에 strong event가 있으면 그 oldest 위치를 first event, newest 위치를 last event로 설정한다.
- **박동 후 100표본:** Strong event가 나타날 때 첫 위치와 마지막 위치를 갱신하고, DSCR flip을 세며, 매 sample의 `abs(sample-baseline)>>ENERGY_SHIFT` code를 saturation sum에 더한다.
- **폭(width):** pre+post 좌표계에서 first strong-event 위치와 last strong-event 위치의 차이를 width proxy로 사용한다. Event가 없으면 0이다. Post window가 끝날 때 fixed wide condition 또는 adaptive width reference와의 deviation condition을 평가한다.
- **복잡도(complexity):** 같은 관찰 구간에서 DSCR sign-flip count를 6-bit 범위로 포화시킨 값이다. 별도 DSCR path의 개별 flip pulse를 beat-window 단위로 다시 묶는 점이 다르다.
- **에너지:** 각 sample의 baseline absolute deviation을 shift해 8-bit code로 만들고 합산한 뒤 다시 scaling하여 6-bit `qrs_energy_code`로 포화한다. 첫 valid beat가 energy reference를 초기화하고 이후 reference는 difference를 shift한 step으로 천천히 따라간다. Reference 대비 deviation이 locked condition을 넘을 때 energy abnormal event가 된다.
- **Pre-QRS activity:** 박동 직전에 strong event가 하나 이상 있었는지, flip이 반복되었는지, pre-energy sum이 충분했는지를 captured pre state로 판단해 `pre_qrs_bump_spike`를 만든다.

Post window 종료 clock에는 width·complexity·energy를 evaluation register에 저장한다. 다음 pipeline stage에서 adaptive reference와 비교 조건을 계산하고, 그 다음 clock에 `qrs_maf_valid_spike`, width/complexity/energy abnormal spike와 pre-QRS bump를 출력한다. Width/energy reference도 이 output stage에서 old reference를 기준으로 next reference를 commit한다. `segment_start`는 pre history, window state, reference와 pipeline을 모두 초기화한다. 이 순서를 통해 “old observation→captured evaluation→condition→output/next reference”가 분리된다.

**4) RBBB-like terminal delay.** 이 경로는 QRS LIF의 `beat_spike`와 별개로 `strong_event|slope_valid`의 활동도가 0→1로 바뀌고 onset refractory가 비어 있을 때 QRS-like onset을 연다. Onset 이후 `qrs_age`를 accepted sample마다 증가시키고 activity가 나타난 age 80–160의 10-sample 간격 hypothesis bit를 표시한다. 동시에 90–170의 terminal zone에서 activity sample 수를 센다. Activity가 일정 gap 동안 사라지거나 최대 observation window에 도달하면 관찰을 끝낸다.

가장 늦게 표시된 hypothesis가 matched-width proxy가 되고, width condition과 terminal activity-count condition을 각각 wide/terminal event로 바꾼다. 두 조건이 함께 참이면 beat-level `rbbb_like_beat_spike`다. 60초 동안 wide·terminal·combined beat count와 width/terminal 조합 count를 누적한다. Segment boundary에서는 combined beat가 반복되었는지, PNN mismatch가 지나치게 높지 않은지, 설정에 따라 high-RDM suppression 조건을 확인한 뒤 segment-level evidence를 낸다. 따라서 한 beat의 늦은 activity가 곧 segment class evidence가 되지 않고 반복성과 rhythm context를 거친다. 구현 module은 `rbbb_qrs_delay_bank`다.

| 관찰 대상 | 필요한 이유 | 구체적인 하드웨어 처리 | 생성 상태 | 사용 위치 | 구현 모듈 |
|---|---|---|---|---|---|
| 기울기 방향 | 파형 굴곡과 방향 전환 | filtered reference error, retained valid sign, sign transition | slope/flip spike | Snapshot morphology count | `dscr_spike_counter` |
| Peak 진폭 | beat별 positive peak 압축 | predicted beat window, threshold-bank sample code, maximum retention, post hold | peak code+valid spike | code sum/count | `ram_peak_accumulator` |
| QRS 폭 | 활동 구간 길이 proxy | pre/post finite window의 first/last strong-event position | width value/abnormal spike | class state+Final aggregate | `qrs_maf_neuron` |
| QRS 복잡도 | beat-window 내 반복 굴곡 | DSCR flip count를 6-bit saturation code로 확정 | complexity code/spike | morphology contribution | `qrs_maf_neuron` |
| QRS 에너지 | 기준 대비 beat energy deviation | per-sample absolute deviation code sum, adaptive reference | energy code/spike | morphology contribution | `qrs_maf_neuron` |
| Pre-QRS 활동 | main event 직전 작은 활동 | 120-sample strong/flip/energy history snapshot | bump spike | Snapshot/Final counter | `qrs_maf_neuron` |
| Terminal delay | 넓고 늦은 활동의 반복 | onset age, terminal-zone activity, repeated beat count, rhythm gate | beat/segment event | class score gate | `rbbb_qrs_delay_bank` |

*표 6. Morphology/amplitude path의 actual finite-state mechanism.*

**통합 해석 경계.** DSCR, RAM, QRS MAF와 RBBB-like path는 waveform을 압축한 engineering proxy다. Lead와 database scale의 영향을 받을 수 있고, 표준 morphology measurement나 RBBB clinical detector가 아니다. 현재 source에서 안전하게 확인되지 않는 parameterized aggregate state total은 `UNRESOLVED_FROM_STATIC_AUDIT`로 유지한다.

## 3.4 60초 Snapshot과 30분 Final Membrane

개별 사건 하나는 class를 결정하기에 충분하지 않다. RR mismatch 하나는 일시적 noise일 수 있고, 높은 peak code 하나는 lead scale의 영향일 수 있으며, sign flip 하나는 정상 QRS 굴곡에서도 발생할 수 있다. 따라서 event를 바로 label로 바꾸지 않고 60초와 30분 두 단계에서 결합한다.

**60초 Snapshot 누적.** `class_score_neurons`는 PNN match/mismatch, RDM code, DSCR slope/flip, RAM code, ectopic pair, QRS MAF abnormal events, pre-QRS bump와 RBBB-like segment event를 입력으로 받는다. 각 event에는 네 class에 대한 fixed signed contribution이 있다. Positive contribution은 해당 class state를 올리는 excitation, negative contribution은 내리는 inhibition이다. Rhythm과 morphology local state는 분리되어 갱신되다가 readout에서 더해진다. 동시에 beat 수, event 수, code sum과 일정 비율/평균 조건을 segment counter로 유지한다.

60,000번째 accepted sample에서 top FSM이 `segment_done`을 만들면 counter의 old value만 읽어 마지막 event를 놓치지 않도록 `*_count_next`를 snapshot register에 확정한다. Class readout pipeline은 event-level delta, segment-level ratio/average delta와 structural gate를 순서대로 membrane에 반영하고 네 64-bit Snapshot class state를 strict WTA로 비교해 local `pred_class/pred_valid`를 만든다. 다음 `segment_start`에서 local history·counter·adaptive reference를 reset한다. 반면 이미 확정된 Snapshot winner와 집계 특징은 `final_membrane_layer`가 받아 30분 state에 더한다.

**Local winner의 의미.** Snapshot prediction은 “이 60초에서 어느 class state가 가장 컸는가”라는 국소 결론이다. 30분 label이 아니므로 한 Snapshot이 불규칙해 보여도 나머지 29개가 다른 class를 지속적으로 지지하면 final decision은 달라질 수 있다.

**Final Membrane 입력과 누적.** 매 `snapshot_done`에서 Final layer는 다음을 old long-window state에 더한다.

- 네 Snapshot winner count
- beat, PNN mismatch, ectopic-pair, QRS MAF, RBBB-like와 pre-QRS count
- abnormal/rhythm/morphology aggregate
- RDM valid count와 code sum, RAM code sum

30번째 Snapshot에서도 현재 segment 값을 포함한 `*_next`를 `dec_*` register에 먼저 capture한다. 다음 pipeline stages는 이 frozen 30분 aggregate만 사용한다. Base seed는 class별 Snapshot winner count다. 따라서 Final Membrane은 단순 vote에 그치지 않고, winner count가 설명하지 못하는 rhythm/morphology 지속성을 structural evidence와 함께 본다.

**Base membrane과 structural overlay.** Ordering은 `FM_BASE → FM_BASE_APPLY → FM_STRUCT → FM_WTA`로 고정된다.

1. **Base stage:** winner count로 initial class states를 만들고 strong/weak base pattern과 aggregate condition을 평가한다.
2. **Guard:** 특정 base winner가 반대되는 morphology/rhythm evidence와 충돌할 때 잘못된 과도한 이동을 억제한다.
3. **Rescue:** winner count만으로 밀렸지만 특정 class를 지지하는 persistence와 margin 조건이 함께 있을 때 그 class를 보강한다.
4. **Veto/inhibition:** 충분한 반대 증거가 있을 때 기존 class state를 낮춰 단순 vote의 실패 mode를 제한한다.
5. **Silent-AFF:** Snapshot AFF winner가 거의 나타나지 않는 형태에서도 낮은 overt activity와 long-window aggregate의 특정 조합을 보고 AFF state를 보강하고 competing CHF state를 억제한다.

이 logic은 임상 rule 이름이 아니라 locked classifier의 bounded membrane correction이다. Threshold 숫자는 locked include/config가 authority이며 본문에서 새로 해석하지 않는다.

**설명용 장시간 예.** 30개 중 한 60초 구간에서 noise 때문에 irregular event가 많아 ARR local winner가 되었더라도, 나머지 구간의 winner와 rhythm/morphology aggregate가 일관되게 다른 state를 지지하면 그 한 구간이 final을 자동 지배하지 않는다. 반대로 약한 local evidence가 여러 구간에 반복되면 winner count와 aggregate state 양쪽에 누적되어 long-term persistence가 된다. 이 예 역시 state behavior 설명이며 임상 case가 아니다.

**Final WTA.** Structural membrane 네 개를 NSR부터 best로 두고 CHF, ARR, AFF 순서로 strict `>` 비교한다. Equal value는 기존 best를 교체하지 않으므로 tie priority는 NSR→CHF→ARR→AFF 순서로 결정적이다. `final_pred`는 가장 큰 class ID, 네 `final_mem`은 WTA 직전의 signed structural states다. Prediction뿐 아니라 네 membrane까지 36/36 비교하면 같은 winner가 우연히 나왔지만 내부 state가 다른 오류도 잡을 수 있다.

```text
for each 60-second Snapshot:
    capture local winner and feature counters
    winner_count[class] += 1
    long_feature_sums    += current_snapshot_features

after Snapshot 30:
    base_mem       = function(winner_counts)
    guarded_mem    = apply_base_guards_rescue_veto(base_mem, long_feature_sums)
    structural_mem = apply_persistence_and_silent_conditions(guarded_mem)
    final_pred      = strict_WTA(structural_mem)
    final_mem[4]    = structural_mem[4]
```

[근거: CLM-003; `components/digital_accelerator/rtl/core/class_score_neurons.v`; `components/digital_accelerator/rtl/final_membrane_layer.v`; digital commit `c6b80de...`]

## 3.5 Streaming state와 하드웨어 구현 방식

Top `snn_ecg_30min_final_top`은 `IDLE→CORE_RESET→SEG_START→RUN→SEG_DONE→FLUSH→COMMIT→DONE`의 FSM으로 동작한다. RUN에서만 `sample_valid&&sample_ready`를 accepted sample로 만들고, 일반 sample 뒤에는 process-hold cycle을 두며 60,000번째 accepted sample에서 boundary로 이동한다. Segment readout pipeline이 끝나도록 flush한 다음 COMMIT에서 Final layer에 Snapshot을 전달한다. 30번째 commit만 `chunk_done`을 세워 final output을 유효화한다.

Hardware-friendly 특성은 다음과 같다.

- Sample마다 signed subtraction, shift, comparison과 작은 accumulator만 갱신한다.
- Beat-centered history는 QRS MAF 120표본 lookback과 100표본 post-window처럼 finite하다.
- 60초 counter는 segment start에서 reset되고 Final Membrane만 30 Snapshot에 걸쳐 지속된다.
- Floating-point inference, matrix multiplier, inference-time learning memory가 없다.
- Pure RTL은 complete 30분 raw waveform을 저장하지 않는다 [CLM-023].

```text
1,800,000 samples × 12 bits
= 21,600,000 bits
= 2,700,000 bytes
≈ 2.7 MB (decimal)
```

이 값은 **avoided full raw-input window storage**다. 실제 synthesized register total, MicroBlaze memory, measured memory saving, power 또는 speed evidence가 아니다. 일부 parameterized group은 static audit만으로 exact aggregate width를 안전하게 합산하지 않았으므로 절감률도 계산하지 않는다.

| 시간 유지 범위 | 대표 상태 | 갱신/확정 시점 | Reset 범위 |
|---|---|---|---|
| 표본값 사이 | previous sample, filter, QRS membrane, refractory | accepted sample | core/segment별 module 규칙 |
| 박동 사이 | token age, RR predictor, RDM prev RR, ectopic reference | beat 또는 rhythm tick | segment start |
| 박동 관찰 구간 | RAM peak code, QRS MAF pre/post state, delay age | sample/beat/window end | beat/segment |
| 60초 | event/code counters, Snapshot class membranes | event와 segment_done | next segment start |
| 30분 | winner counts, aggregate sums, Final Membranes | snapshot_done/chunk_done | first segment final_clear |

*표 7. Persistent state의 시간 범위. [근거: CLM-023; `tables/streaming_state_inventory.csv`; `docs/STREAMING_STATE_MEMORY_KR.md`]*

표 7은 state가 없다는 뜻이 아니라 state 크기가 1,800,000-sample raw array로 증가하지 않는다는 뜻이다. 이 state hierarchy가 sample→beat→Snapshot→Final로 정보를 옮기는 핵심 hardware architecture다.

# 4. MATLAB/XMODEL 및 FPGA 구현

## 4.1 AFE·ADC 모델 검증

Digital core 앞단은 실제 electrode PCB가 아니라 두 단계 model-based verification으로 구성된다. MATLAB은 HPF, IA gain, 60 Hz notch, LPF와 ±1.65 V 12-bit ADC의 nominal intent를 검토한다. 대표 NSR·CHF·ARR·AFF 60초 record에서 rail hit와 clipping은 모두 0%였고 최소 headroom은 ARR record의 1.019633440086 V였다 [CLM-015, CLM-024].

| Class | ADC code range | Clipping | Minimum headroom |
|---|---:|---:|---:|
| NSR | 1909–2525 | 0% | 1.264815619462 V |
| CHF | 1701–2739 | 0% | 1.092577998716 V |
| ARR | 1265–2626 | 0% | 1.019633440086 V |
| AFF | 1612–2452 | 0% | 1.299625888976 V |

*표 8. MATLAB nominal dynamic range. 네 selected record의 model result이며 physical rail measurement가 아니다. [근거: CLM-015, CLM-024; owner 서민우; `components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv`]*

표 8은 nominal chain이 representative input을 ADC range 안에 두었다는 것을 보이지만 component tolerance나 전체 population을 보장하지 않는다. MATLAB package는 class별 stage output, signed decimal, offset-binary와 two’s-complement reference vector를 SHA256 manifest와 함께 제공한다.

SystemVerilog XMODEL은 emulator waveform과의 정합성, PLI·offset/wander·R/C mismatch·finite GBW/VOS·ADC non-ideal을 검토한다. 36개 60초 segment의 settling 후 emulator↔XMODEL mean RMS difference는 1.95 LSB, lag는 0이었다. 이는 model-to-model waveform alignment이고 local steep-QRS deviation이 없다는 뜻은 아니다 [CLM-014].

| XMODEL 항목 | 결과 | 무엇을 보여주는가 | 보여주지 않는 것 |
|---|---:|---|---|
| Emulator↔XMODEL | mean RMS 1.95 LSB, lag 0 | 36×60초 waveform model agreement | bit-exact analog·physical accuracy |
| PLI | 60 Hz 0.92 mV, 50 Hz 118 mV RMS residual | 60 Hz notch target와 50 Hz sensitivity | 50 Hz retuned system 성능 |
| R/C mismatch | 0.1%에서 CMRR 100.7 dB, 1%에서 80.0 dB | modeled component sensitivity | direct 30분 final_pred sweep |
| ADC non-ideal | representative final_pred 15/16 유지 | 4 chunks×4 perturbations sensitivity | 모든 ADC non-ideal 불변성 |
| Long signed stream | final input SHA 36/36 | AFE output와 digital input byte identity | label correctness |

*표 9. XMODEL stress와 handoff 결과. [근거: CLM-012, CLM-014, CLM-025~CLM-027; owner 이수환; `components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md`]*

표 9의 PLI, mismatch와 ADC regression은 서로 다른 test unit이므로 하나의 broad “analog robustness” 수치로 합치지 않는다. Physical AFE PCB, ADC silicon, transistor/post-layout와 live-electrode acquisition은 수행하지 않았다 [CLM-020].

## 4.2 RTL/IP/FPGA 구현

Digital implementation은 Python locked reference→full-top RTL/XSim→Vivado implementation→AXI/IP-XACT package→Vitis/MicroBlaze replay→Nexys A7 FPGA 순서로 진행되었다. Pure RTL profile은 accelerator core만 포함하고 MicroBlaze profile은 processor, local memory, UART, sample feeder와 core를 모두 포함한다.

| Implementation scope | LUT | FF/register | BRAM | DSP | Timing evidence |
|---|---:|---:|---:|---:|---:|
| Pure RTL accelerator | 9,719 | 5,038 | 0 | 0 | WNS 8.184 ns |
| MicroBlaze full-replay system | 12,494 | 8,494 | 16 | 3 | setup WNS 0.097 ns |

*표 10. FPGA resource와 timing closure. [근거: CLM-008, CLM-009, CLM-010; `components/digital_accelerator/reports/final/final_metrics.json`]*

Pure RTL의 0 BRAM/0 DSP는 fixed-width streaming datapath와 일관된다. 그러나 BRAM 0 하나만으로 full-window 비저장을 증명하지 않으며, 그 근거는 direct RTL state inventory다. MicroBlaze의 BRAM/DSP는 software와 replay infrastructure를 포함하므로 pure core와 감소율을 계산할 수 없다. WNS는 implementation constraint 아래의 slack이며 한 30분 decision의 processing latency가 아니다.

AXI wrapper는 sample feeder와 control/status register를 통해 start, valid/ready, final class와 membrane을 연결하고 IP-XACT `component.xml`로 package된다. MicroBlaze application은 locked `.mem`을 sample feeder로 전달하고, core가 1,800,000 accepted samples와 30 Snapshot을 처리한 뒤 final output을 UART로 반환한다. 이는 digital IP integration proof이지 external electrode acquisition이나 fabricated SoC가 아니다.

## 4.3 End-to-end 기능 등가성 검증

End-to-end verification은 “36/36”이라는 같은 표기 안에서도 서로 다른 질문을 분리한다.

1. **Input SHA256 36/36:** XMODEL AFE에서 만든 final-test chunk와 board-replay `.mem`이 byte-for-byte 같은가?
2. **Canonical AFE→RTL pred/mem 36/36:** 같은 bytes를 `sample_gap_cycles=2`로 넣었을 때 locked RTL이 digital golden class와 membrane을 재현하는가?
3. **XSim→FPGA pred/mem 36/36:** packaged board system이 XSim expected state를 재현하는가?
4. **Label 29/36:** 그 output class가 public-dataset ground truth와 같은가?

![그림 7. 기능 등가성](../figures/final/FIG-08_signed_stream_handoff.svg)

*그림 7. Byte identity, canonical RTL identity와 label correctness의 분리.*

| 비교 경계 | 결과 | 증명하는 것 | 증명하지 않는 것 |
|---|---:|---|---|
| AFE chunk↔board input | SHA256 36/36 | input byte identity | physical analog accuracy |
| AFE chunk↔locked RTL | pred/mem 36/36 | canonical state reproduction | 100% label accuracy |
| XSim↔FPGA | pred/mem 36/36 | packaged digital functional equivalence | clinical validity |
| FPGA output↔label | 29/36 | 현 dataset classification | domain generalization |

*표 11. End-to-end equivalence와 accuracy의 경계. [근거: CLM-011~CLM-013, CLM-021]*

Prediction과 four membrane을 함께 비교하는 이유는 class winner만 우연히 같고 내부 score가 다른 hidden-state mismatch를 검출하기 위해서다. 따라서 FPGA 36/36은 구현 정확성을 강하게 지지하지만 classifier의 label accuracy를 100%로 만들지 않는다.

# 5. 실험 결과

## 5.1 분류 성능

Train은 61/68=89.71%로 fitting 상태를 확인했다. Validation 32/32=100.00%는 Final Membrane model selection에 사용한 결과이므로 final generalization으로 승격하지 않는다 [CLM-006]. Lock 후 한 번 평가한 final-test 30분 chunk는 29/36=80.56%, macro F1 80.44%, balanced accuracy 80.56%였다 [CLM-004]. 같은 final partition을 source record별 majority로 합치면 16/19=84.21%, macro F1 80.80%, balanced accuracy 88.19%였다 [CLM-005].

![그림 8. 분류 결과](../figures/final/FIG-10_classification_summary.svg)

*그림 8. Validation은 selection-only로 분리하고 locked final 결과를 중심에 둔 분류 요약.*

| Evaluation | Correct/total | Accuracy | Macro F1 | 해석 |
|---|---:|---:|---:|---|
| Train | 61/68 | 89.71% | — | fitting evidence |
| Validation | 32/32 | 100.00% | — | model selection only |
| Locked final chunk | 29/36 | 80.56% | 80.44% | primary held-out result |
| Final record-majority | 16/19 | 84.21% | 80.80% | same partition aggregation |

*표 12. Classification result. [근거: CLM-004~CLM-007; `components/digital_accelerator/reports/final/final_metrics.json`]*

Record-majority의 상승은 일부 record에서 chunk error가 aggregation으로 완화되었음을 보이지만 독립 test 재현은 아니다. Class별 final chunk confusion은 표 13과 같다.

| Ground truth\Prediction | NSR | CHF | ARR | AFF | Recall |
|---|---:|---:|---:|---:|---:|
| NSR | 9 | 0 | 0 | 0 | 100.00% |
| CHF | 0 | 6 | 0 | 3 | 66.67% |
| ARR | 2 | 0 | 7 | 0 | 77.78% |
| AFF | 1 | 0 | 1 | 7 | 77.78% |

*표 13. Locked final-test chunk confusion matrix. 행은 truth, 열은 prediction이다. [근거: CLM-004]*

CHF 3건이 AFF로, ARR 2건이 NSR로, AFF 각 1건이 NSR/ARR로 분류되었다. CHF recall 66.67%가 가장 낮고 class당 support가 9이므로 accuracy 하나로 균질한 class 성능을 주장하지 않는다.

## 5.2 Mixed-signal 및 디지털 통합 결과

MATLAB nominal은 representative input이 ADC rail 안에 있음을 보였다. XMODEL RMS/lag는 continuous-solver model과 digital emulator가 settling 이후 유사한 waveform을 냈음을 보였다. SHA256 36/36은 그 결과로 만든 digital bytes가 board input까지 바뀌지 않았음을 보였고, canonical AFE→RTL 36/36은 동일 bytes에서 class와 membrane state가 보존되었음을 보였다.

이 네 결과는 차례로 nominal range, model agreement, input integrity, digital state reproduction을 답한다. 어느 하나도 physical electrode-to-silicon accuracy나 clinical efficacy를 직접 증명하지 않는다. 반대로 model-based analog 한계가 남더라도 already-fixed bytes에 대한 RTL state reproduction은 유효하다.

## 5.3 하드웨어 구현 결과

Pure RTL implementation에서 positive WNS와 0 BRAM/0 DSP를 확인했고, packaged MicroBlaze system도 positive setup WNS를 보였다. Board 36 cases 모두 1,800,000 accepted samples, 30 Snapshot와 one decision을 완료했으며 final_pred와 final_mem이 각각 36/36 expected output과 일치했다. Label comparison은 같은 output에 대해 29/36이다.

Accelerator latency, throughput, CPU speedup, power, energy와 board timing은 아직 integrated evidence로 import되지 않았다. 상태는 `PENDING_EXTERNAL_BENCHMARK_IMPORT`다 [CLM-018]. Exact C++ baseline이 외부에서 진행 중이어도 commit, input hash, environment, raw result와 measurement scope를 검증하기 전에는 수치를 인용하지 않는다.

| Benchmark item | 현재 상태 | Formal import 조건 |
|---|---|---|
| CPU/Exact C++ latency | Pending | compiler·host·input hash·raw runs |
| RTL processing cycles/throughput | Pending | accepted-sample와 decision scope |
| Speedup/realtime headroom | Pending | same work unit 비교 |
| Power/energy | Pending | estimated와 measured 분리 |
| Board latency/power | Pending | transport와 compute 분리 계측 |

*표 14. Accelerator benchmark pending status. Null은 zero가 아니다. [근거: CLM-018; `benchmarks/accelerator_benefit/README.md`]*

# 6. 종합 논의와 한계

## 6.1 설계적 차별성과 기술적 의의

본 설계의 차별성은 “ECG를 FPGA에서 빠르게 계산했다”는 문장보다 신호를 시간 계층과 상태 전이로 재정의한 데 있다. 인접 표본값은 사건 신호가 되고, 사건의 반복은 박동이 되며, 박동 사이 시간은 rhythm state가 된다. 박동 중심 finite window는 peak·width·complexity·energy·terminal activity로 압축되고, 이 local evidence가 60초 Snapshot과 30분 Final Membrane으로 올라간다. 독자는 한 input sample이 final class에 영향을 주는 경로를 각 register/counter boundary에서 추적할 수 있다.

SNN-inspired 구조의 의미도 여기서 분명해진다. Dense waveform을 보존하는 대신 사건에 반응하고, membrane-like accumulator와 threshold로 temporal evidence를 decision에 반영한다. QRS generic detector는 leak 구조를 갖고 locked setting에서는 leak=0이며, Final Membrane은 positive/negative class state와 WTA를 사용한다. 이는 biological fidelity가 아니라 event/state hardware abstraction이다.

Hardware 기술성은 fixed-width arithmetic뿐 아니라 cadence와 commit ordering에 있다. Event encoder의 previous-sample update, QRS old→next membrane, PNN sequential scan, QRS MAF의 multi-cycle evaluation, segment counter의 `*_next` capture, Final `BASE→STRUCT→WTA`가 모두 정확한 clock ordering을 요구한다. XSim, Vivado, IP-XACT와 board membrane 36/36은 이 ordering이 packaged system에서도 보존되었음을 보여준다.

Reproducibility는 재실행 여부만이 아니라 어떤 source와 claim을 사용했는지까지 포함한다. Fixed component commits, dataset DOI/hash, artifact manifest, ownership matrix와 SAFE/CAREFUL/FORBIDDEN registry가 report sentence의 범위를 고정한다. 긴 path와 hash는 Appendix B/C로 이동하여 본문은 engineering reasoning에 집중시켰다.

## 6.2 결과의 해석 범위와 향후 과제

가장 큰 과학적 한계는 class와 source DB가 결합된 database–class confounding이다. Record-wise split은 direct leakage를 막지만 acquisition/lead/population signature를 제거하지 않는다. Final test는 36 chunks·19 records이고 AFF는 한 record이므로 chunk 균형이 subject diversity를 뜻하지 않는다. 다음 우선순위는 같은 acquisition device·lead·protocol의 frozen multi-class external test다.

Architecture 차원에서는 Snapshot-only, unguarded vote, base membrane과 full structural overlay를 동일 untouched cohort에서 비교한 report-ready ablation이 없다. 그러므로 Final Membrane의 정확도 향상량을 수치로 주장하지 않는다. Frozen variants와 same split/cadence를 사용한 ablation이 필요하다.

Analog와 physical 범위는 MATLAB/XMODEL까지다. PCB parasitic, electrode impedance, ADC INL/DNL, post-layout와 fabricated silicon을 포함하지 않는다. Physical AFE/ADC code를 같은 signed interface로 획득해 reference vector 및 XMODEL과 비교한 뒤, standard-cell synthesis·layout·STA·measurement로 확장해야 한다.

| 한계 | 영향 | 현재도 유효한 evidence | 다음 검증 |
|---|---|---|---|
| DB–class confounding | physiology/domain 분리 불가 | locked classification·RTL equivalence | same-acquisition/cross-domain cohort |
| 제한된 record support | class uncertainty | one-time 36-chunk result | larger independent records |
| Ablation 부재 | time hierarchy 기여량 미확정 | locked full architecture | frozen Snapshot/base/full variants |
| Physical AFE/ADC 부재 | 실제 robustness 미확정 | MATLAB/XMODEL handoff | PCB/ADC code measurement |
| ASIC/post-layout 부재 | area/power sign-off 없음 | FPGA feasibility | P&R·extracted STA·silicon |
| Clinical validation 부재 | diagnosis claim 불가 | engineering result | approved prospective protocol |
| Benchmark pending | speed/energy benefit 미확정 | resource/timing closure | formal benchmark import |

*표 15. 한계, 영향, 남는 evidence와 구체적인 다음 검증. [근거: CLM-017~CLM-020, CLM-022]*

이 한계는 generalization과 physical/commercial claim을 제한하지만 same bytes에서 확인한 RTL/IP/FPGA 기능 등가성을 소급해 무효화하지 않는다. 본 prototype은 clinically validated diagnostic device, fabricated silicon 또는 상용 wearable보다 우수한 제품이 아니다.

# 7. 결론

본 연구는 장시간 ECG 네 class 분류를 위해 1 ms 표본값에서 시작해 박동, 60초 Snapshot, 30분 Final Membrane으로 이어지는 다중 시간축 SNN-inspired RTL architecture를 제안하였다. 인접 표본값의 signed difference와 adaptive event bank가 파형 변화 pulse를 만들고, QRS membrane·threshold·refractory가 여러 pulse를 한 beat로 묶는다. PNN은 recurring RR hypothesis와 다음 interval의 match를 보고, RDM은 연속 RR absolute difference를 level code로 바꾸며, ectopic path는 adaptive reference에 대한 early–late 교대를 검출한다.

파형 경로는 filtered slope sign을 보존해 DSCR direction change를 검출하고, predicted beat window에서 RAM maximum amplitude code를 남긴다. QRS MAF는 박동 전 120표본과 후 100표본의 strong event 위치, sign flip, baseline deviation energy와 pre-QRS activity를 pipeline으로 확정한다. RBBB-like path는 독립 activity onset, terminal window와 repeated wide/delay pattern을 segment evidence로 만든다. 이 사건과 code는 fixed signed contribution으로 Snapshot class states를 갱신하고 30개 winner count와 aggregate가 Final base/guard/rescue/veto/silent overlay를 거쳐 deterministic WTA output이 된다.

Strict record-wise locked final 결과는 chunk 29/36=80.56%, record-majority 16/19=84.21%였다. Pure RTL은 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP와 positive WNS를 보였고, AFE input SHA, canonical AFE→RTL과 FPGA pred/mem은 각 경계에서 36/36 일치하였다. Complete 1,800,000-sample raw window를 저장하지 않지만 2.7 MB는 회피한 raw-input window일 뿐 measured saving이 아니다.

따라서 기여는 임상 진단이나 고속·저전력 우월성 주장이 아니라, 장시간 ECG evidence가 실제 register·counter·window·FSM을 거쳐 final class가 되는 과정을 설명 가능하고 재현 가능한 semiconductor IP로 완성한 데 있다. Database confounding, physical/clinical/ASIC gap, ablation과 benchmark pending을 다음 검증 과제로 남긴다.

# 참고문헌

[1] U.S. Food and Drug Administration, “De Novo Classification Request for ECG App (DEN180044),” 2018. https://www.accessdata.fda.gov/cdrh_docs/reviews/DEN180044.pdf

[2] ACC/AHA/HRS, “2018 Guideline on Bradycardia and Cardiac Conduction Delay,” 2018. https://doi.org/10.1161/CIR.0000000000000628

[3] PhysioNet, “MIT-BIH Normal Sinus Rhythm Database v1.0.0,” doi:10.13026/C2NK5R. https://physionet.org/content/nsrdb/1.0.0/

[4] PhysioNet, “BIDMC Congestive Heart Failure Database v1.0.0,” doi:10.13026/C29G60. https://physionet.org/content/chfdb/1.0.0/

[5] PhysioNet, “MIT-BIH Arrhythmia Database v1.0.0,” doi:10.13026/C2F305. https://physionet.org/content/mitdb/1.0.0/

[6] PhysioNet, “MIT-BIH Atrial Fibrillation Database v1.0.0,” doi:10.13026/C2MW2D. https://physionet.org/content/afdb/1.0.0/

[7] Goldberger AL et al., “PhysioBank, PhysioToolkit, and PhysioNet,” Circulation 101(23), 2000. https://doi.org/10.1161/01.CIR.101.23.e215

[8] Open Data Commons, “Attribution License v1.0.” https://opendatacommons.org/licenses/by/1-0/

# 부록 A. 핵심 수치

| 범주 | 수치 | Claim/scope |
|---|---|---|
| 입력 | signed 12-bit, 1 kSPS | CLM-002 |
| 시간축 | 60,000 samples×30 | CLM-003 |
| Final chunk | 29/36=80.56%, F1 80.44% | CLM-004 |
| Record majority | 16/19=84.21%, F1 80.80% | CLM-005 |
| MATLAB | clipping 0%, min headroom 1.019633440086 V | CLM-015,024 |
| XMODEL | mean RMS 1.95 LSB, lag 0 | CLM-014 |
| Integration | SHA 36/36, gap=2 pred/mem 36/36 | CLM-012,013 |
| Pure RTL | 9719 LUT, 5038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns | CLM-008,009 |
| MicroBlaze | 12494 LUT, 8494 reg, 16 BRAM, 3 DSP, WNS 0.097 ns | CLM-010 |
| Board | pred/mem 36/36; label 29/36 | CLM-011 |
| Streaming | avoided raw window 2,700,000 bytes≈2.7 MB | CLM-023 |
| Benchmark | `PENDING_EXTERNAL_BENCHMARK_IMPORT` | CLM-018 |

# 부록 B. Claim/evidence mapping

| 본문 범주 | Claim | 핵심 evidence |
|---|---|---|
| Identity/interface/time hierarchy | CLM-001~003 | digital report, top RTL, input contract |
| Evaluation/protocol | CLM-004~007,016~017 | lock/split/final metrics |
| Hardware/board | CLM-008~011 | Vivado and board artifacts |
| XMODEL/integration | CLM-012~014,025~027 | stress report and comparison CSV |
| MATLAB | CLM-015,024 | dynamic-range CSV/vector manifest |
| Pending/forbidden | CLM-018~022 | claim registry/benchmark placeholder |
| Streaming memory | CLM-023 | direct RTL inventory |

전체 machine-readable path, fixed commit, owner와 limitation은 `reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv` 및 `source_of_truth/claim_registry.csv`를 따른다.

# 부록 C. 주요 artifact와 재현 절차

고정 component commit은 MATLAB `907f7e1...`, XMODEL `4756a508...`, digital `c6b80de...`다. PhysioNet raw source는 `tools/fetch_physionet_datasets.py`와 `tools/verify_physionet_datasets.py`로 저장소 밖에 복원한다. Integrated figure는 `tools/generate_integrated_figures.py`로 생성하며 report/repository checker를 연속 실행한다.

직접 architecture evidence:

- Event/QRS/RR: `components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v`, `qrs_lif_detector.v`, `pnn_rhythm_predictor.v`
- Rhythm: `rdm_variability_neuron.v`, `ectopic_pair_neuron.v`
- Morphology: `dscr_spike_counter.v`, `ram_peak_accumulator.v`, `qrs_maf_neuron.v`, `rbbb_qrs_delay_bank.v`
- Snapshot/final: `class_score_neurons.v`, `snn_ecg_30min_final_top.v`, `final_membrane_layer.v`
- State inventory: `tables/streaming_state_inventory.csv`

```powershell
python tools/generate_integrated_figures.py
python tools/check_integrated_technical_report.py
python tools/check_integrated_repository.py
```

Application form의 page 제한, 소속·지도교수·서명 등 개인정보 입력은 이 public repository 밖의 private HWP 편집 단계에서 수행한다.
