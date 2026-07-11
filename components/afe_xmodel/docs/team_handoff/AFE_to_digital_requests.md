# 디지털팀(양건)에 요청/확인할 사항 — AFE 측 검증 진행 관련

> 작성: 이수환(AFE) · 2026-07-06 · 배경: 검증 1.1~2.4 진행 중, 아래 항목이 있으면 재현/확장이 완결됨

## A. 최우선 — 1.5 완전 확장을 위한 30분 windowing 정의
1. **`fullrec_afe_30min_annotation_valid_balanced` 데이터셋 빌드 스크립트(또는 window→sample-offset 매핑 표)** 를 공유해 주세요.
   - 각 `<rec>_30min_wXXX.mem`가 원본 연속 스트림의 **어느 1,800,000 샘플 구간**인지(stride, `annotation_valid_balanced` 선택 규칙).
   - 현재 우리는 mitdb ARR(레코드=정확히 30.1분)만 `w000=첫 1.8M 샘플`로 명확해, ARR 105/118/214 3개를 **최신 locked model에서 bit-exact 재현 완료**(final_pred·final_membrane 일치). 위 매핑이 있으면 NSR/CHF/AFF 다-윈도우 chunk까지 **36개 전부 bit-exact 확장** 가능.
2. 그 30분 .mem이 **우리가 전달한 `fullrec_afe`(afe_emu 파이프라인)를 슬라이스한 것인지**, 아니면 별도 재생성인지 확인 부탁. 전자면 "최신 모델 성능=우리 AFE 경로 위" 링크가 bit-exact로 확정됩니다.

## B. 1.4 (emu↔XModel 정합) 대상 정렬
3. emu↔실제 XModel 정합 검증의 "final_test 36" 기준으로 우리는 **test split에서 클래스당 9개(60s 세그)** 를 선택했습니다. 팀원이 canonical한 세그 리스트(또는 대표 record/offset)를 갖고 있으면 공유해 정렬하겠습니다. (없으면 우리 선택으로 진행.)

## C. 2.1 (ADC non-ideal → 분류결과) final_pred 채우기
4. ADC offset/gain/noise/jitter를 주입한 신호를 **최신 locked model에 태워 final_pred 변화**를 채우려 합니다. 우리 XSim 하네스(`docs/integration_latest/xsim_harness/`: manifest+wrapper+prj)를 정본 실행 경로로 사용해도 되는지 확인 부탁. (OK면 우리가 바로 확장.)

## D. 스코프 합의 (요청이라기보다 확인/합의)
5. **2.2**: 본 설계는 **60Hz(한국 mains) 대상**이며 50Hz 환경은 notch center retune이 필요 — 최종 보고서에 scope 문구로 함께 명시하는 것에 합의 부탁.
6. 입력이 이미 digitized public .mem이라 **원본 raw sensor 단일패스 검증은 공동 범위 밖** — 기존 한계 문구 유지에 합의 부탁.

## 참고 — 우리가 이미 완료해 전달 가능한 산출물
- 1.1 clipping/headroom(전 DB): `docs/afe_stress/clipping_report.csv` — 60s chunk 1,200개 clipping 0.
- 2.1 ADC non-ideal / 2.3 R-peak 보존: `docs/afe_stress/` (CSV+보고서).
- 1.5 최신 locked model 재통합(ARR bit-exact): `docs/integration_latest/`.

---

## 회신 반영 (2026-07-09, 건이형 답신 처리 완료)
- **A(windowing):** 규칙 `start = 2000 + chunk_id×1,800,000` 수령 → 우리 `fullrec_afe`에서 36 chunk 생성, `board_replay_36_cases.csv`의 `mem_sha256`과 **36/36 bit-identical** 확인. XSim **final_pred 36/36 · final_mem 35/36 exact** 재현. → `docs/integration_latest/`(§3.5), 생성기 `scripts/gen_30min_chunks.py`. **1.5 완결.**
- **B(1.4 정렬):** canonical list 없음 확인 → test split 클래스당 9세그로 진행, 재현성 CSV 남김: `docs/afe_stress/afe_val36_segment_list.csv`.
- **C(final_pred harness):** `docs/integration_latest/xsim_harness/`를 정본으로 사용. 2.1(ADC non-ideal) final_pred는 이 harness로 30분 chunk에 섭동 주입해 재실행(진행). 1.2(mismatch)는 30분 아날로그 XModel 비현실적 → 등가 논증(아래 보고서).
- **D(scope):** 확정 문구를 `docs/afe_stress/AFE_xmodel_verification.md`(2.2·검증한계)에 그대로 반영.
