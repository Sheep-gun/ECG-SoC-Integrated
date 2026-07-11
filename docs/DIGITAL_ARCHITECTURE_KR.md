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

이 architecture claim은 `CLM-023`으로 등록돼 있으며, direct RTL signal/group inventory는 `tables/streaming_state_inventory.csv`, 상세 해석은 `docs/STREAMING_STATE_MEMORY_KR.md`에 있다. 회피한 full raw-input window는 `1,800,000×12=21,600,000 bit=2,700,000 byte≈2.7 MB decimal`이다. 이는 MicroBlaze runtime memory나 정확한 synthesized memory 절감량이 아니다. 보고서용 상세 블록도는 `figures/final/FIG-12_detailed_digital_architecture.svg`이며 conceptual grouping임을 caption에 명시한다.

## 60-second Snapshot Readout

1 kSPS 조건에서 60,000 samples가 한 Snapshot interval을 이룬다. Interval 동안 누적된 rhythm/morphology evidence가 네 class의 local score/readout으로 변환된다. Snapshot은 일시적인 local evidence를 보존하지만 단독으로 최종 long-window decision을 확정하지 않는다.

## 30-minute Final Membrane Readout

Final Membrane layer는 30개의 Snapshot readout을 signed class state에 누적한다. Positive/negative evidence와 guarded update가 class별 persistence를 반영하며, 30번째 Snapshot 이후 WTA가 NSR/CHF/ARR/AFF 중 하나를 선택한다. Locked model ID는 `structural_guarded_silent_aff_1008710`이고 parameter hash는 digital fixed snapshot에 기록돼 있다.

## SNN-inspired라는 표현의 경계

Event occurrence가 sparse state update를 유발하고 membrane-like state가 시간에 따라 누적되므로 neuromorphic/SNN-inspired라고 부른다. 그러나 repository evidence는 backpropagation으로 학습된 deep spiking network, STDP, neuron biophysics 또는 biological equivalence를 지원하지 않는다.

## Determinism and cadence

RTL output은 accepted sample sequence와 control timing에 대해 deterministic하다. Integrated AFE-to-RTL result의 canonical board-facing condition은 `sample_gap_cycles=2`다. Noncanonical fast harness에서 관찰된 cadence-specific debug 결과를 final claim에 사용하지 않는다.

## Architecture evidence

- Top/final layer: `components/digital_accelerator/rtl/snn_ecg_30min_final_top.v`, `rtl/final_membrane_layer.v`
- Locked parameters: `components/digital_accelerator/configs/final_submission_locked_model.json`
- Architecture narrative: `components/digital_accelerator/FINAL_REPORT_KR.md`
- Final equivalence: `components/digital_accelerator/reports/final/final_metrics.json`
- Persistent-state inventory: `tables/streaming_state_inventory.csv`
- Detailed architecture: `figures/final/FIG-12_detailed_digital_architecture.svg`
