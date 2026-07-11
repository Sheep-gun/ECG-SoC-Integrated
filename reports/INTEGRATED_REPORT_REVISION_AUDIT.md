# Integrated report revision audit

## 상태

- Revision status: `PENDING_REPORT_COMMIT`
- Branch: `codex/award-level-integrated-report`
- Pre-revision HEAD: `4bd8c51d4b15de0b45410db84ab52a29e5082893`
- Pre-revision commit title: `Finalize publication-readiness audit`
- Final report revision commit: `PENDING`
- Audit-finalization commit: `PENDING_BRANCH_HEAD`

본 audit는 보고서 변경을 먼저 커밋한 뒤 final report revision commit을 기록하고 완료 상태로 전환한다.

## 분량과 구조

| 항목 | 개정 전 | 개정 후 |
|---|---:|---:|
| 원고 전체 문자 수 | 33,966 | 38,542 |
| 초록 문자 수 | 79 | 1,149 |
| 결론 문자 수 | 1,344 | 1,341 |
| 본문 장 | 10 | 11 |
| 본문 표 | 11 | 14 |
| 참조 그림 | 11 | 12 |
| 부록 | A/B | A/B/C |

개정 후 원고는 25,000~40,000자 목표 범위에 있으며 초록은 900~1,300자 범위다. 결론은 수치·기여·경계를 세 문단으로 종합한다.

## 확장·재구성한 절

- 서론을 배경·기존 범위·장시간 필요성·목표·6개 기여·범위로 분리했다.
- MATLAB→XMODEL→signed interface→digital→RTL/IP/FPGA와 contributor handoff를 하나의 signal/evidence flow로 묶었다.
- Dataset source/version/DOI/license, raw-data fetch/hash, 60초/30분 construction, strict record-wise lock과 confounding을 재현 가능한 방법 장으로 정리했다.
- Digital 장을 adaptive event, QRS LIF, beat/RR, PNN, RDM, DSCR, RAM, ectopic pair, QRS MAF, RBBB-like, Snapshot, Final Membrane, structural overlay, WTA의 16개 절로 완성했다.
- MATLAB nominal 표와 XMODEL stress 표를 분리하고 모든 승격 수치에 개별 claim을 연결했다.
- Streaming-state inventory, top FSM, Snapshot/final control, pure RTL, IP-XACT, MicroBlaze와 FPGA를 구현 장에서 분리했다.
- 결과 뒤에 종합 논의 장과 대회 심사용 창의성·기술성·완성도 장을 신설했다.
- 한계 10항목마다 영향, 여전히 유효한 evidence와 구체적인 다음 실험을 연결했다.

## 문단 병합·중복 제거

- Architecture 설명과 결과 장에 반복되던 Snapshot/Final Membrane 정의는 제4장에서 완전 설명하고 이후에는 해석만 남겼다.
- Board 36/36, AFE SHA 36/36, canonical RTL 36/36의 반복 문장을 표 12의 서로 다른 검증 경계로 통합했다.
- Pure RTL/MicroBlaze 자원 설명을 표 9로 통합하고 scope와 WNS 경계를 한 번만 해석했다.
- Dataset confounding 반복을 방법 장의 정의, 논의 장의 영향, 한계 장의 다음 실험으로 기능 분리했다.
- README의 연구 배경·문제·기여 반복을 축약하고 report link→identity→architecture→metrics→structure→limitations→reproducibility→benchmark 순서로 재작성했다.

## 그림과 표

사용 그림은 `FIG-01`~`FIG-12` 전부이며 각 Markdown image path가 존재한다. `FIG-04`는 다중 시간축 상위 구조, `FIG-12`는 verified RTL block의 report-facing conceptual grouping으로 구분한다.

본문 표 14개는 목표, interface, dataset/license, split, feature/event blocks, MATLAB nominal, XMODEL stress, streaming state, RTL/MicroBlaze resources, classification, confusion matrix, integration equivalence, benchmark pending, limitations/future validation을 담당한다. 각 표는 caption, evidence annotation과 후속 해석을 갖는다.

## Claim 변경

추가한 claim:

- `CLM-024`: 대표 MATLAB record 최소 headroom 1.019633440086 V
- `CLM-025`: XMODEL 60/50 Hz PLI RMS residual 0.92/118 mV
- `CLM-026`: XMODEL 0.1%/1% mismatch CMRR 100.7/80.0 dB
- `CLM-027`: 대표 ADC non-ideal locked-RTL regression final_pred 15/16

Narrowing:

- Headroom은 selected nominal records로 한정하고 physical rail 보증을 금지했다.
- PLI는 60 Hz target과 50 Hz retuning 미검증을 분리했다.
- Mismatch CMRR는 direct 30분 final_pred sweep이 아님을 명시했다.
- ADC 15/16은 대표 4 chunks×4 perturbations이며 universal invariance가 아님을 명시했다.
- WNS는 processing latency, 36/36 equivalence는 classification accuracy, 2.7 MB는 measured memory saving으로 해석하지 못하게 했다.

제거한 numeric statement:

- 검증된 source를 가진 수치는 제거하지 않고 개별 claim으로 좁혔다.
- 미등록 benchmark 값은 개정 전·후 모두 포함하지 않았다.
- `54.01 ms`, `33.3 MSPS`, `33,300×`, `0.099 W`, `5.35 mJ`는 checker의 금지 값으로 유지한다.

## 미해결 evidence

- Database–class confounding과 same-acquisition cohort 부재
- AFF final-test source record support 1
- Snapshot-only/base/full structural ablation의 report-ready source-of-truth 부재
- Physical AFE/ADC, live electrode와 clinical validation 부재
- ASIC/post-layout/fabricated-silicon 결과 부재
- Exact parameterized streaming-state aggregate width 미산출
- Exact C++ baseline, accelerator latency/throughput/speedup/power/energy와 board timing/power 미수입

Benchmark status는 `PENDING_EXTERNAL_BENCHMARK_IMPORT`이며 모든 integrated benchmark value field는 `null`이다.

## Checker 결과

- `tools/check_integrated_technical_report.py`: PASS — 472 rules, 0 conflicts, chars 38,542, abstract 1,149, conclusion 1,341
- `tools/check_integrated_repository.py`: PASS — 211 rules, 0 conflicts
- `git diff --check`: PASS

## 향후 공식 HWP 작업

본 원고를 공식 양식의 page/field 제한에 맞게 축약·재배치하고, 소속·지도교수·서명 등 개인정보는 private HWP에서만 입력한다. External benchmark가 정식 import되기 전에는 pending 표를 수치 표로 대체하지 않는다.
