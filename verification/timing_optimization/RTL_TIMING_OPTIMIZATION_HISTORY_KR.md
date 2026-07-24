# RTL timing bottleneck 분석과 pipeline 최적화 이력

## 근거 범위와 commit 관계

최종 고정 RTL은 `Sheep-gun/SNN-ECG-4-Class-Classifier`의 `c6b80de19cdcad5b7e43fe7835588b629d847f75`이다. 다음 두 개발 commit은 `git merge-base --is-ancestor`로 각각 최종 고정 commit의 ancestor임을 확인했다.

| 단계 | Commit | 역할 | 직접 Git history 근거 |
|---|---|---|---|
| 병목 pipeline 수정 | `c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa` | 주요 조합 경로 관측 후 구조적 분할 | upstream `docs/timing_bottlenecks.md`와 해당 commit의 RTL diff |
| timing margin 추가 개선 | `5e2e5d0a46be47d8086b8642e055066079bfa4e6` | 남은 얇은 경로를 추가 분할하고 flush timing 정렬 | upstream `docs/timing_bottlenecks.md`와 해당 commit의 RTL diff |
| 최종 고정 RTL | `c6b80de19cdcad5b7e43fe7835588b629d847f75` | 최종 구현·XSim·FPGA replay 근거 | `design/digital/`과 `design/digital/reports/final/final_metrics.json` |

원본 `docs/timing_bottlenecks.md`는 `c7c75cf...`에서 생성되고 `5e2e5d0...`에서 갱신됐지만, 최종 제출용 저장소 정리 과정에서 삭제됐다. 따라서 이 문서는 해당 파일이 현재 component에 존재한다고 주장하지 않고, 다음 Git history 원본을 통합 보고서에서 추적할 수 있도록 정리한다.

- `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier/blob/c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa/docs/timing_bottlenecks.md`
- `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier/blob/5e2e5d0a46be47d8086b8642e055066079bfa4e6/docs/timing_bottlenecks.md`

## Critical path 관측

초기 주요 병목은 `class_score_neurons` 내부의 `rdm_level_spike → pred_class` 조합 경로였다. 당시 OOC 10 ns 분석에서 이 경로는 약 90 logic levels와 52개 CARRY4를 포함한 긴 누산·비교·winner-take-all 경로였고, `class_score_neurons`가 약 17.5k LUT의 주요 자원·timing hotspot으로 기록됐다.

약 17.5k LUT는 **최적화 전 historical OOC hotspot 수치**다. 최종 구현의 Pure RTL 9,719 LUT와는 RTL revision과 보고 범위가 다르므로 감소율이나 직접 면적 비교에 사용하지 않는다.

## 구조적 pipeline 분할

목표 clock을 느슨하게 바꾸는 대신, 긴 경로의 계산과 상태 확정 시점을 다음과 같이 나눴다.

| 수정 | 구조적 의미 |
|---|---|
| C24/global readout과 class WTA 분리 | RDM 사건에서 최종 클래스 선택까지 이어지던 same-cycle 경로를 끊었다. |
| `segment_done`의 `*_next` counter capture | pipeline 지연을 넣어도 마지막 표본의 사건과 계수값이 Snapshot에 포함되도록 했다. |
| C24 event/gate/score delta 등록 | 사건·gate·점수 증분을 레지스터에 보존한 뒤 장시간 막전위에 적용했다. |
| RDM·RAM exact lookup table | threshold/code 산술과 진폭 곱셈 경로를 동일 정수 결과의 case lookup으로 바꿨다. |
| Snapshot update–adjust–commit 분리 | 점수 갱신, 구조 보정, 최종 저장을 서로 다른 단계로 나누면서 signed 상수와 동점 우선순위를 유지했다. |
| RBBB gate timing 정렬 | 지연된 score commit 뒤의 값을 보도록 gate 평가 시점을 pipeline에 맞췄다. |
| QRS MAF 다중-cycle 처리 | 120-bit combinational scan을 timestamp FIFO 기반 순차 평가로 바꿨다. |
| PNN predictor center 등록 | predictor center를 레지스터에 보존하고 `case` lookup으로 계산했다. |
| Final Membrane pairwise stage | margin 계산과 class WTA를 pairwise 단계로 분리했다. |
| ARR scale/commit과 flush 정렬 | ARR scale·commit을 등록하고 post-segment flush가 모든 지연 단계를 기다리도록 맞췄다. |

`5e2e5d0...`에서는 C24 gate pending 경로와 ARR high-irregular 판정도 추가 분할했다. 이후 최종 고정 RTL에서는 `class_score_neurons.v`의 `score_finalize_*`, `score_scaled_*`, `score_commit_*`, `c24_gate_delta_pending`, `qrs_maf_neuron.v`의 timestamp FIFO, `pnn_rhythm_predictor.v`의 `hyp_center` case lookup과 registered center, `final_membrane_layer.v`의 staged readout으로 이 구조가 이어진다.

## Timing 재검증과 기능 등가성

검증 순서는 `critical path 관측 → pipeline 분할 → timing 재검증 → 기능 등가성 확인`이었다.

1. Historical OOC 보고서에서 원래의 `rdm_level_spike → pred_class` 경로가 더 이상 발견되지 않고 10 ns OOC setup/hold 검사를 통과했음을 확인했다. 이 OOC 수치는 개발 이력이며 최종 implementation 수치와 혼합하지 않는다.
2. Pipeline 수정 직후 Git history의 Python–RTL 표본 검사는 train·validation·test 각 2개 사례에서 `pred_mismatch=0`, `mem_mismatch=0`을 기록했다.
3. 최종 고정 commit의 full-top XSim은 locked final-test 36개에서 `final_pred`와 `final_mem` mismatch가 모두 0이었다.
4. 최종 구현은 Pure RTL WNS 8.184 ns, MicroBlaze 전체 system setup WNS 0.097 ns를 기록했다. 두 값은 각각 다른 implementation 범위다.
5. FPGA replay 36개에서도 `final_pred` 36/36, `final_mem` 36/36 일치를 확인했다.

따라서 기존 RDM-to-prediction critical path는 구조적으로 제거됐고, pipeline으로 상태 확정 시점을 바꾼 뒤에도 고정 정수 기준 모델·RTL·FPGA의 기능 등가성을 유지하면서 최종 timing closure를 달성했다. 이는 과거 OOC 자원값을 최종 자원값으로 승격하거나, WNS를 처리 지연시간으로 해석한다는 뜻이 아니다.

## 최종 직접 근거

- `design/digital/rtl/core/class_score_neurons.v`
- `design/digital/rtl/core/qrs_maf_neuron.v`
- `design/digital/rtl/core/pnn_rhythm_predictor.v`
- `design/digital/rtl/final_membrane_layer.v`
- `design/digital/rtl/snn_ecg_30min_final_top.v`
- `design/digital/reports/final/final_metrics.json`
