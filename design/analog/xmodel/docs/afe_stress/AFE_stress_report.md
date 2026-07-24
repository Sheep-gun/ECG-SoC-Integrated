# AFE 추가 검증 보고서 — Clipping / ADC non-ideal / R-peak 보존

> 제27회 반도체설계대전 · 한양대 · 담당: 이수환(AFE) · 2026-07-06
> 디지털팀 검증 요청 중 **XModel 재실행 없이 즉시 가능한 3건**(1.1 / 2.1 / 2.3)을 완료.
> 재현: `python3 scripts/{verify_clipping,adc_nonideal,rpeak_timing}.py` (WSL, numpy/scipy)
> 산출: `docs/afe_stress/{clipping_report,adc_nonideal_test,rpeak_timing_test}.csv`

---

## 1.1 전체 final dataset clipping / headroom 검증 — ✅ 통과

**대상:** (a) full-record 전체 DB **127 record**(연속 스트림, 총 35.9억 샘플) · (b) 분류기 실입력인 strict60_large **60초 세그 1,200개**(train 800 / val 200 / test 200).

| 대상 | records | clipping(head 2s 제외) | clip ratio | code 범위 | 판정 |
|---|---|---|---|---|---|
| **60s chunk — test** | 200 | **0** | 0% | 748 ~ 3091 | ✅ headroom 748/1004 LSB |
| **60s chunk — val** | 200 | **0** | 0% | 1111 ~ 2986 | ✅ |
| **60s chunk — train** | 800 | **0** | 0% | 533 ~ 3583 | ✅ headroom 512+ LSB |
| full-record DB | 127 | 2,577 / 35.9억 | **0.00007%** | — | ✅ (<0.01%) |

**핵심 결론**
- **분류기가 실제로 소비하는 60초 chunk는 test/val/train 1,200개 전부 clipping = 0.** code 최댓값이 full-scale(4095) 대비 500 LSB 이상 여유 → 포화 없음. (팀원 "final_test 36 / 136 chunk에서 포화 안 하나?" 질문에 대한 직접 답 = **0**.)
- 연속 full-record(수 시간 raw Holter 포함)에서도 **127개 중 124개가 clipping 0**. 나머지 3개만 극소 발생:

| record | clip | 전체 샘플 | ratio |
|---|---|---|---|
| CHF/chf15 | 2,338 | 71.97M(~20h) | 0.0032% |
| AFF/04015 | 169 | 36.8M | 0.00046% |
| AFF/08455 | 70 | 36.8M | 0.00019% |

- 3건 모두 수 시간 raw 스트림의 **순간적 대진폭 아티팩트**가 ADC를 잠깐 rail시킨 것이며, 전부 통과기준 0.01% 미만. chf15는 기존에도 지목된 CHF outlier 계열. **분류기 60s 스냅샷 경로에는 영향 없음(위 1,200개 0 clipping).**

> **보고 문구:** "분류기 입력 60s chunk 1,200개 전수에서 ADC clipping = 0(headroom ≥500 LSB). 연속 full-record 35.9억 샘플에서도 clip ratio 0.00007%로 0.01% 기준을 크게 하회하며, 127 record 중 124개가 정확히 0."

---

## 2.1 ADC non-ideal sweep — ✅ 강건

**대상:** test 60s 세그 200개. AFE는 검증된 emulator, ideal 12-bit ADC 기준 대비 offset/gain/noise/jitter 주입. 지표는 세그 평균(HPF 정착 2s 제외).

| case | ADC code RMS편차[LSB] | max편차[LSB] | 추가 clipping | R-peak timing 영향 |
|---|---|---|---|---|
| ideal | 0 | 0 | 0 | — |
| offset ±1/2/5 LSB | 1 / 2 / 5 | 동일 | **0** | 없음(순수 code shift) |
| gain +0.5% | 0.64 | 3.1 | **0** | 없음 |
| gain ±1% | 1.14 | 5.7 | **0** | 실질 무변화 |
| noise 0.5/1/2 LSB rms | 0.64 / 1.08 / 2.04 | ~9 | **0** | p95 shift ≤0.1 ms |
| jitter 10/50/100 µs | 0.15 / 0.39 / 0.68 | ~12 | **0** | ≤0.02 ms |

**결론:** 현실 범위 ADC 비이상성(offset·gain·noise·jitter) 어디서도 **추가 clipping 0**, code 편차는 주입량에 비례한 **LSB 수준**에 그치고, R-peak timing은 사실상 불변(200세그 전체에서 매칭 실패 0~2건). 1 kSPS라 100 µs 지터도 sub-sample(0.1샘플)이라 영향 미미.
※ `final_pred`(분류결과) 변화는 SNN 통합경로(검증 1.5) 필요 → 표는 AFE/ADC 측 지표까지. RR-error 열의 대형 이상치(≈2 s)는 불규칙 리듬 1개 세그의 peak 개수 불일치에 따른 정렬 아티팩트(중앙값 0 ms).

> **보고 문구:** "ADC offset ±5 LSB, gain ±1%, noise 2 LSB rms, jitter 100 µs 범위에서 추가 clipping 0, code 편차 LSB급, R-peak timing 불변 — 이상 ADC 가정에만 의존하지 않음을 확인."

---

## 2.3 R-peak timing / morphology preservation — ✅ 보존

**대상:** raw/test 200개. 원본 ECG(.mem) vs AFE 출력에서 R-peak 위치·RR interval 비교(정착 2s 제외).

| 지표 | 값 |
|---|---|
| R-peak 매칭율 (중앙값 / 최저) | **100% / 96.1%** |
| timing shift 중앙값 (= AFE 군지연) | **1.0 ms** |
| timing 지터 std (중앙값) | **0.43 ms** |
| RR interval error (중앙값) | **0.0 ms** |
| QRS 대역 상관도 (중앙값) | 0.936 |

**결론:** AFE 대역통과가 R-peak을 **1 ms 고정 군지연 + 0.43 ms 지터**로 통과시키며, RR interval 오차 중앙값 0 ms. 즉 waveform 상관도(0.90~0.97)뿐 아니라 **SNN이 쓰는 이벤트/리듬 feature(R-peak 위치·RR)까지 보존**. 통과기준(R-peak shift <5~10 ms, RR err <10 ms) 충족.
※ 일부 AFF(세동) 세그는 리듬 자체가 불규칙해 검출기 기준 매칭율이 96%대로 내려가고 RR-error 이상치가 발생하나, 이는 AFE 왜곡이 아니라 원본 리듬 특성.

> **보고 문구:** "AFE는 R-peak을 1 ms 군지연·0.43 ms 지터로 보존(RR 오차 중앙값 0 ms) — 형태 상관뿐 아니라 QRS/rhythm timing feature까지 유지."

---

## 남은(XModel 필요) 항목
1.5(최신 locked model 재통합, **최우선**) · 1.4(emu↔XModel 36세그) · 1.3(offset/wander stress) · 1.2(R/C mismatch) · 2.2(50Hz) · 2.4(op-amp non-ideal). 2.1의 `final_pred` 열도 1.5에서 채워짐.
