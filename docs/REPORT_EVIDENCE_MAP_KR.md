# 통합 기술보고서 evidence map

공식 보고서의 설명 순서와 실제 artifact의 추적 관계를 정의한다. 본문은 처음 읽는 심사자가 표본→사건→박동→RR/파형 특징→60초 Snapshot→30분 Final Membrane→최종 class를 따라가도록 일곱 장으로 구성한다. 세부 경로·commit·owner·limitation은 `reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv`가 machine-readable authority다.

| 보고서 장 | 핵심 질문 | 주 근거 | 해석 경계 |
|---|---|---|---|
| 1. 서론 | 무엇을 왜 설계했는가 | `docs/PROBLEM_DEFINITION_KR.md`, `docs/CONTRIBUTIONS_AND_NOVELTY_KR.md` | 임상 진단이나 상용 우월성 주장이 아님 |
| 2. 전체 시스템과 평가 방법 | 데이터와 세 component가 어떻게 연결되는가 | `source_of_truth/upstream_commits.yaml`, `source_of_truth/ownership_matrix.csv`, dataset·split artifact | record-wise split이 database–class confounding을 제거하지 않음 |
| 3. 디지털 아키텍처 | 표본이 어떤 RTL state transition을 거쳐 class가 되는가 | digital `rtl/`, FIG-12~14, `tables/streaming_state_inventory.csv` | trained deep SNN·STDP·online learning이 아닌 SNN-inspired event/state architecture |
| 4. 구현 | MATLAB/XMODEL intent와 RTL/IP/FPGA가 어떻게 검증되는가 | MATLAB/XMODEL 결과, Vivado/IP-XACT/MicroBlaze artifact | model-based analog 검증은 physical AFE/ADC 검증이 아님 |
| 5. 결과 | 정확도·등가성·자원이 각각 무엇을 뜻하는가 | `final_metrics.json`, SHA/equivalence/board result | 36/36 기능 등가성을 100% label accuracy로 해석하지 않음 |
| 6. 논의와 한계 | 기여가 무엇이며 어디까지 유효한가 | claim registry, confounding/limitation 문서 | benchmark는 독립 import 전까지 pending |
| 7. 결론 | 무엇을 완성했고 무엇이 남았는가 | 앞 장의 registered evidence | physical·clinical·ASIC claim 금지 |

## 제3장 직접 RTL 감사 범위

- 박동·리듬: `ecg_event_encoder_adaptive.v`, `qrs_lif_detector.v`, `pnn_rhythm_predictor.v`, `rdm_variability_neuron.v`, `ectopic_pair_neuron.v`
- 파형·진폭: `dscr_spike_counter.v`, `ram_peak_accumulator.v`, `qrs_maf_neuron.v`, `rbbb_qrs_delay_bank.v`
- 계층적 판정: `class_score_neurons.v`, `snn_ecg_30min_final_top.v`, `final_membrane_layer.v`

본문은 module 이름을 목차로 노출하지 않고 기능 질문으로 묶는다. 다만 각 설명의 마지막에는 실제 module과 evidence path를 남겨 구현 사실을 추적할 수 있게 한다.

## 공식 HWP 이관 규칙

1. SAFE claim만 단정형으로 쓰며 CAREFUL claim은 같은 문단에서 범위를 제한한다.
2. Board 36/36은 기능 등가성, final 29/36은 label 정확도로 분리한다.
3. Benchmark 값은 `PENDING_EXTERNAL_BENCHMARK_IMPORT`가 해제되기 전까지 넣지 않는다.
4. 개인정보·서명·공식 신청서 필드는 private HWP에서만 작성한다.
