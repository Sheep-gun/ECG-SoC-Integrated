# Streaming state 및 full-window buffer 회피 근거

## 결론과 claim 범위

`CLM-023`의 허용 문구는 다음과 같다.

> 본 pure RTL accelerator는 1,800,000-sample 전체 raw input window를 저장하지 않고, sample-by-sample 방식으로 고정 크기 event/state와 Final Membrane을 갱신한다.

이는 fixed digital commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`의 top/controller, event/QRS/RR/morphology block, Snapshot counter, `final_membrane_layer`를 정적으로 조사한 architecture claim이다. 정확한 runtime memory나 MicroBlaze system memory 측정값이 아니며, FF 5,038 또는 BRAM 0만으로 추론한 주장도 아니다.

## 직접 RTL evidence

Top은 `sample_valid && sample_ready`일 때만 `core_sample_valid`를 만들고, accepted sample마다 event/state를 갱신한다. `timer_mem`이 `SNAPSHOT_SAMPLES-1`과 같을 때 60,000-sample boundary를 만들고, `snapshot_index`가 `SNAPSHOTS_PER_CHUNK-1`과 같을 때 30-Snapshot chunk를 종료한다. raw sample array의 주소를 1,800,000개 유지하는 구조는 없다.

Persistent state는 다음과 같이 유한하다.

- event encoder의 이전 sample, delta, calibration histogram/bank
- QRS LIF membrane 및 refractory counter
- beat/RR predictor와 variability state
- DSCR/R-peak/ectopic/QRS MAF/RBBB-like morphology state
- Snapshot 구간의 event/evidence counters와 class-score state
- 네 class의 Final Membrane vote/evidence accumulator
- guard/rescue/veto/silent-AFF 및 WTA pipeline state
- top controller, sample counter, Snapshot index와 interface state

각 signal/group, width, reset, update 조건은 `tables/streaming_state_inventory.csv`에 연결했다. 대형 parameterized `class_score_neurons`처럼 단일 total width를 안전하게 산출하지 않은 항목은 `UNRESOLVED_FROM_STATIC_AUDIT`로 표시한다.

## Avoided full raw-input window storage

입력 계약의 한 final decision window는 1 kSPS × 1,800 s = 1,800,000 samples이고 sample width는 signed 12 bit다.

`1,800,000 samples × 12 bits = 21,600,000 bits = 2,700,000 bytes ≈ 2.7 MB decimal`

이 값의 label은 **avoided full raw-input window storage**다. 실제 synthesized register total, MicroBlaze BRAM 사용량, board runtime memory 또는 power/latency benchmark가 아니다. Pure RTL의 state total도 unresolved group이 있으므로 2.7 MB와 정확한 “절감률”을 계산하지 않는다.

## 경계

- QRS MAF의 120-sample finite lookback과 adaptive histogram은 raw 30분 window buffer가 아니다.
- MicroBlaze replay의 processor/local memory/UART는 pure accelerator 밖에 있으므로 본 claim에 포함하지 않는다.
- `BRAM=0`은 implementation consistency evidence일 뿐 단독 proof가 아니다.
- Benchmark 수치는 별도 반입 근거를 사용한다. 본 메모리 분석의 2.7 MB 회피값만으로 latency, throughput, power 또는 energy를 계산하지 않는다.
