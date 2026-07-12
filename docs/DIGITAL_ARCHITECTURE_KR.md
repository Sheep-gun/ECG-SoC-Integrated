# Digital architecture

## 입력과 state update

Digital top은 1 kSPS signed 12-bit sample, valid/segment control을 받아 sample-by-sample state를 갱신한다. 전체 30분 raw waveform을 저장하지 않고 다음과 같은 fixed-size event/state를 유지한다.

- delta/slope와 up/down/strong event
- beat/QRS timing state
- RR variability와 rhythm-related counters
- R-peak amplitude accumulation
- ectopic-like pair evidence
- QRS morphology/width-related evidence
- class score/membrane state

연산은 정수 counter, comparator, shift/add, signed accumulator와 deterministic control로 구성된다. Floating-point, inference-time learning memory와 전체-window buffer를 요구하지 않는다.

## Dense model의 하드웨어 부담과 본 구조의 대응

본 구조는 generic dense CNN/RNN/MLP를 FPGA에 그대로 옮긴 것이 아니라 ECG domain knowledge를 사건·박동·리듬·파형 형태 증거로 바꾸고 고정 폭 정수 상태에 누적하는 domain-specific streaming accelerator다.

| 일반적인 dense 구현 부담 | 본 설계의 대응 |
|---|---|
| multiplier와 대규모 MAC | comparator, counter, shift/add, signed accumulator |
| DSP 의존 가능성 | 고정 Pure RTL 구현 DSP 0 |
| weight·activation buffer와 BRAM 요구 가능성 | 추론 시 가중치 메모리 없음, 고정 Pure RTL 구현 BRAM 0 |
| 전체 window 또는 대규모 feature tensor | 고정 크기 상태를 표본값 단위로 갱신 |
| 짧은 구간과 장시간 판정의 연결 | 60초 Snapshot 30개를 Final Membrane에 누적 |

이는 구조 대응표이지 실제 dense 기준선과의 측정 비교가 아니다. 정확도·속도·전력·면적 우월성, sparse event rate 또는 전력 절감률을 주장하지 않는다. 2.7 MB는 측정 절감량이 아니라 회피한 30분 raw-input window storage다 [CLM-008, CLM-023].

이 architecture claim은 `CLM-023`으로 등록돼 있으며, direct RTL signal/group inventory는 `tables/streaming_state_inventory.csv`, 상세 해석은 `docs/STREAMING_STATE_MEMORY_KR.md`에 있다. 회피한 full raw-input window는 `1,800,000×12=21,600,000 bit=2,700,000 byte≈2.7 MB decimal`이다. 이는 MicroBlaze runtime memory나 정확한 synthesized memory 절감량이 아니다. 보고서용 흐름도는 `figures/final/FIG-12_digital_signal_flow.svg`이며 conceptual grouping임을 caption에 명시한다.

## 60-second Snapshot Readout

1 kSPS 조건에서 60,000 samples가 한 Snapshot interval을 이룬다. Interval 동안 누적된 rhythm/morphology evidence가 네 class의 local score/readout으로 변환된다. Snapshot은 일시적인 local evidence를 보존하지만 단독으로 최종 long-window decision을 확정하지 않는다.

## 30-minute Final Membrane Readout

Final Membrane layer는 30개의 Snapshot readout을 signed class state에 누적한다. Positive/negative evidence와 guarded update가 class별 persistence를 반영하며, 30번째 Snapshot 이후 WTA가 NSR/CHF/ARR/AFF 중 하나를 선택한다. Locked model ID는 `structural_guarded_silent_aff_1008710`이고 parameter hash는 digital fixed snapshot에 기록돼 있다.

## SNN-inspired라는 표현의 경계

Event occurrence가 sparse state update를 유발하고 membrane-like state가 시간에 따라 누적되므로 neuromorphic/SNN-inspired라고 부른다. 그러나 repository evidence는 backpropagation으로 학습된 deep spiking network, STDP, neuron biophysics 또는 biological equivalence를 지원하지 않는다.

## Determinism and cadence

RTL output은 accepted sample sequence와 control timing에 대해 deterministic하다. Integrated AFE-to-RTL result의 canonical board-facing condition은 `sample_gap_cycles=2`다. Noncanonical fast harness에서 관찰된 cadence-specific debug 결과를 final claim에 사용하지 않는다.

## Timing을 위한 pipeline 경계

고정 RTL의 pipeline은 단순 처리량 증가가 아니라 긴 조합 경로를 끊으면서 마지막 사건과 상태 확정 순서를 보존하도록 설계됐다. C24/global readout과 WTA, Snapshot update–adjust–commit, RDM·RAM lookup, QRS MAF timestamp FIFO, PNN predictor center, Final Membrane pairwise WTA와 post-segment flush가 그 경계다. 개발 이력과 최종 기능 등가성은 `docs/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md`와 CLM-048에 기록한다.

## Architecture evidence

- Top/final layer: `components/digital_accelerator/rtl/snn_ecg_30min_final_top.v`, `rtl/final_membrane_layer.v`
- Locked parameters: `components/digital_accelerator/configs/final_submission_locked_model.json`
- Architecture narrative: `components/digital_accelerator/FINAL_REPORT_KR.md`
- Final equivalence: `components/digital_accelerator/reports/final/final_metrics.json`
- Persistent-state inventory: `tables/streaming_state_inventory.csv`
- Digital signal flow: `figures/final/FIG-12_digital_signal_flow.svg`
