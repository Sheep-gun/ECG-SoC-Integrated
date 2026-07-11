# 향후 private HWP 보고서 evidence map

본 파일은 보고서 본문을 작성하지 않고, 각 장에서 사용할 문장·artifact·claim 경계를 연결한다. 모든 wording은 `claim_registry.csv`의 status를 우선한다.

## 완성 원고와 향후 공식 제출물의 구분

- 완성된 통합 기술 원고: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`
- 원고 검토표: `reports/INTEGRATED_TECHNICAL_REPORT_REVIEW_CHECKLIST.md`
- Machine-readable report evidence map: `reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv`
- 향후 official private HWP/application form: 이 Git 밖에서 작성하며 아직 생성하지 않음

통합 기술 원고는 report-ready technical source이지만 공식 양식의 page limit, 개인정보, 서명과 application field를 포함하지 않는다. 향후 HWP는 아래 chapter mapping과 completed manuscript를 사용해 축약·재배치하되 claim boundary를 유지한다.

| 보고서 장 | 핵심 statement / Claim ID | Supporting artifact | Source/commit | Owner | Status / limitation |
|---|---|---|---|---|---|
| 연구 배경 | wearable ECG의 대표 기능 범위는 AF/sinus screening 중심이며 본 평가와 직접 비교 불가 / EXT-001 | `external_reference_registry.csv` | FDA DEN180044 | 양건(편집) | authoritative background; 제품 성능 수치 비교 금지 |
| 연구 배경 | 장시간 ambulatory monitoring motivation / EXT-002 | `external_reference_registry.csv` | ACC/AHA/HRS guideline | 양건(편집) | conservative context only |
| 문제 정의 | 네 public-dataset class 장시간 분류 / CLM-001 | `PROBLEM_DEFINITION_KR.md` | integrated + digital c6b80de | 양건 | CAREFUL; 임상 확진 금지 |
| 연구 목표 | signed stream을 받는 streaming SNN-inspired IP / CLM-001,002 | `RESEARCH_OBJECTIVES_KR.md` | digital c6b80de | 양건 | SNN-inspired 경계 유지 |
| 연구 방법 | strict source-record-wise lock / CLM-007,016 | `final_submission_locked_model.json`; `STRICT_RECORDWISE_PROTOCOL_KR.md` | digital c6b80de | 양건 | final-test 1회; confounding 미해소 |
| 시스템 구성 | MATLAB→XMODEL→digital→FPGA | `SYSTEM_OVERVIEW_KR.md` | all three fixed commits | 서민우/이수환/양건 | layer ownership 분리 |
| 아날로그 모델 검증 | 대표 nominal clipping 0% / CLM-015 | `afe_dynamic_range_headroom_summary.csv` | MATLAB 907f7e1 | 서민우 | 4 representative records; physical claim 금지 |
| 아날로그 모델 검증 | emu↔XMODEL mean RMS 1.95 LSB / CLM-014 | `AFE_xmodel_verification.md` | XMODEL 4756a508 | 이수환 | model-to-model, not bit-exact |
| 디지털 알고리즘 | 60초 Snapshot + 30분 Final Membrane / CLM-003 | `FINAL_REPORT_KR.md`; RTL sources | digital c6b80de | 양건 | architecture claim |
| Snapshot/Final Membrane 구조 | event/state, integer streaming | `DIGITAL_ARCHITECTURE_KR.md`; `rtl/` | digital c6b80de | 양건 | trained deep SNN claim 금지 |
| 데이터셋·평가 | four DB origins and strict split / CLM-016,017 | `DATASET_AND_EVALUATION_KR.md`; `DATASET_DOMAIN_CONFOUNDING_KR.md` | integrated + PhysioNet refs | 양건 | record leakage와 confounding 구분 |
| 분류 결과 | final-test 29/36=80.56% / CLM-004 | `final_metrics.json` | digital c6b80de | 양건 | primary held-out engineering result |
| 분류 결과 | record-majority 16/19=84.21% / CLM-005 | `final_metrics.json` | digital c6b80de | 양건 | same partition aggregation |
| RTL 회로 구성 | 9719 LUT/5038 FF/0 BRAM/0 DSP / CLM-008 | `final_metrics.json`; Vivado reports | digital c6b80de | 양건 | device/tool specific |
| FPGA/IP 구현 | MicroBlaze system and timing / CLM-010 | `final_metrics.json`; `ip_repo/` | digital c6b80de | 양건 | whole-system scope |
| 통합 검증 | input SHA256 36/36 / CLM-012 | `afe36_sha256_bitidentity.csv` | XMODEL 4756a508 | 이수환 | byte identity only |
| 통합 검증 | gap=2 AFE-to-RTL pred/mem 36/36 / CLM-013 | `afe_locked_rtl_integration_36case_compare.csv` | XMODEL 4756a508 | 이수환 | canonical cadence only |
| 통합 검증 | board pred/mem 36/36 / CLM-011 | `board_replay_36_batch_summary.json` | digital c6b80de | 양건 | functional equivalence, accuracy 아님 |
| 창의성 | multi-timescale temporal hierarchy | `CONTRIBUTIONS_AND_NOVELTY_KR.md` | digital c6b80de | 양건 | speed를 primary novelty로 쓰지 않음 |
| 기술성 | integer streaming + full verification chain | `DIGITAL_ARCHITECTURE_KR.md`; `INTEGRATION_VERIFICATION_KR.md` | all fixed commits | team | engineering prototype |
| 완성도 | commit/hash/claim/ownership control | `artifact_manifest.csv`; `claim_registry.csv` | integrated | 양건 | reproducibility evidence |
| 사업화 가능성 | wearable/edge integration potential | architecture/resource evidence | digital c6b80de | 양건 | commercial/clinical superiority 금지; benchmark 대기 |
| 한계·향후 과제 | confounding, physical gap, benchmark pending | `LIMITATIONS_AND_CLAIM_BOUNDARY_KR.md` | integrated | team | 반드시 명시 |

## HWP 작성 규칙

1. `SAFE` claim만 단정형으로 쓰고 `CAREFUL`은 scope/limitation을 같은 문단에 둔다.
2. `FORBIDDEN` claim은 본문·caption·표·발표 문구 모두에서 사용하지 않는다.
3. 분류 결과 표에서 validation 100%를 primary result로 배치하지 않는다.
4. Board 36/36 표에는 반드시 `functional equivalence`를 표시하고 29/36 accuracy를 별도 행에 둔다.
5. Benchmark package가 import되기 전에는 latency/throughput/speedup/power/energy 칸을 비우거나 pending으로 둔다.
6. 신청서·서명·학번·전화·주소·private email과 최종 HWP/PDF는 이 Git 밖에 둔다.
