# 아날로그-디지털 통합 검증 보고서 (AFE ↔ SNN 디지털 블록)

> 제27회 대한민국 반도체설계대전 · 한양대학교 · 작성: 2026-06-21
> AFE(이수환) ↔ SNN 디지털 블록(양건) 통합 가능성·스펙 일치 검증

## 1. 다중 클래스 ECG로 AFE 검증

팀원이 분류한 실제 4클래스 ECG(`person_data_record_split_strict_varlen`의 `.mem`,
60s@1kSPS)를 아날로그 전압으로 역변환해 AFE에 인가.

| 클래스 | 출처 record | AFE↔원본 상관도 | AFE출력 범위(signed) | 클리핑 |
|---|---|---|---|---|
| NSR | 16539 | 0.972 | −124~+469 | 0 |
| ARR | 105 | 0.905 | −422~+576 | 0 |
| AFF | 04015 | 0.940 | −435~+335 | 0 |
| CHF | chf05 | 0.915 | −265~+424 | 0 |

→ AFE는 4클래스 모두 **충실히 재현(상관도 0.90~0.97), 클리핑 없음**.
   재현(스크립트): `make` 없이 `scripts/run_multiclass.sh` + `analyze_fidelity.py`.

## 2. 디지털 블록 구조 (검증됨)

정식 RTL: `SNN_ECG.srcs/sources_1/new/` (13개 .v, Questa 컴파일 **0 errors / 19 모듈**).
- top: `snn_ecg_3feat_top.v`, core: `snn_ecg_model_a_plus_core.v`
- 파이프라인: `adc_data → ecg_event_encoder(delta/slope→up/down/strong event) →
  qrs_lif_detector(R-peak) → 특징뉴런(rdm_variability, ectopic_pair, qrs_maf_width,
  dscr, ram_peak, pnn_rhythm) → class_score_neurons → winner_id(4클래스)`

## 3. 인터페이스 일치 (AFE ↔ 디지털)

디지털 core 입력 포트: `clk, rst, sample_valid, rhythm_tick, segment_start,
segment_done, signed [11:0] adc_data`. 핵심 파라미터 ADC_WIDTH=12, EVENT_TH=8,
QRS_TH=16, QRS_REF=220 → `.mem` 메타 CSV와 **일치**.

| 항목 | 디지털 기대 | AFE 제공 | 일치 |
|---|---|---|---|
| 해상도/속도 | 12-bit / 1kSPS | 12-bit / 1kSPS | ✅ |
| 진폭 범위 | signed ±수백 코드 | ±수백 코드(.mem과 일치) | ✅ |
| 파라미터(EVENT/QRS_TH/REF) | 8/16/220 | (.mem 메타와 동일 전제) | ✅ |
| **데이터 형식** | **2의보수 signed, 0중심** | **offset-binary unsigned, 2048중심** | ⚠️ 변환 필요 |
| **샘플 핸드셰이크** | sample_valid 펄스(1샘플/clk) | clk_samp(1kHz) 레벨 | ⚠️ 펄스 생성 필요 |

## 4. 통합에 필요한 어댑터 (2개, 경미)

1. **형식 변환**: `adc_signed[11:0] = adc_unsigned − 2048` (= MSB 반전, 1줄).
   미적용 시 ecg_event_encoder의 signed delta가 매 기저선 교차에서 거짓 ±4094 점프 → 오작동.
   (대안: AFE의 SAR ADC를 signed 출력으로 변경.)
2. **sample_valid 생성**: AFE의 매 샘플(negedge clk_samp)마다 core clk 도메인에서
   sample_valid·rhythm_tick 1펄스 생성. segment_start/done으로 구간 경계 표시.

## 5. 통합 검증 가능성 결론

- **Mixed-signal 시뮬(Questa+XModel)**: **가능**. AFE(XModel .sv)와 디지털(Verilog)이
  동일 Questa에서 모두 컴파일됨(검증 완료). 위 어댑터 2개로 AFE 라이브 출력을 core에
  연결하는 통합 tb 작성 가능 → 아날로그→디지털 end-to-end 분류 검증.
- **FPGA(Nexys A7)**: 현재 보드 데모(`nexys_a7_model_s_smoke_top.v`)는 내장 ROM
  (demo_*.mem) **재생 방식**으로 AFE 미연결(독립 데모). 실제 FPGA 통합은 물리 AFE 회로
  → Nexys A7 ADC(XADC/Pmod) → core 경로 필요 (XModel은 비합성 행동모델).

## 6. 권장 다음 단계

1. Mixed-signal 통합 tb 작성: `ecg_afe_xmodel` + `snn_ecg_model_a_plus_core`를 한 tb에
   인스턴스화, `adc_signed=afe_adc−2048` + sample_valid 생성, winner_id로 4클래스 판정 확인.
2. AFE SAR ADC를 signed 출력으로 변경(선택) → 어댑터 1 제거, 직접 연결.
3. FPGA: XADC 인터페이스 블록 추가(물리 AFE 연동 시).

---

## 7. Mixed-signal 통합 시뮬레이션 결과 (최종 실증)

`ecg_afe_xmodel` + `snn_ecg_model_a_plus_core`를 한 TB(`tb/tb_mixed_signal.sv`)에
인스턴스화, 어댑터 2개(offset→signed, sample_valid 생성)로 연결.
AFE를 실시간 0~60초 구동, HPF 정착 후(2초~60초, 58초 창)를 core에 전달, winner_id 판정.

| 클래스 | 디지털 단독(원본 .mem, 동일창) | AFE 통합(라이브) | 일치 |
|---|---|---|---|
| NSR | 2 | 2 | ✅ |
| CHF | 1 | 1 | ✅ |
| ARR | 2 | 3 | ❌ |
| AFF | 3 | 3 | ✅ |

- 통합 메커니즘 완전 동작(Errors 0, pred_valid=1, 클래스당 ~60초). 디지털 단독은
  팀원 공식 RTL 결과 CSV와 4/4 일치(셋업 검증됨).
- **3/4 클래스 분류를 AFE 경로가 정확히 재현** → AFE가 분류기에 투명.
- **ARR만 AFE 경로에서 ARR→AFF 플립**. 전수 격리 실험(scripts/filter_mem.py+run_digref_filt.sh):
  AFE 등가 디지털 필터가 AFE 통합 결과를 **정확히 재현**(full→NSR2 CHF1 ARR3 AFF3) → AFE 효과
  = 순수 선형 필터링(아날로그 아티팩트 아님). 격리: 단일필터(HPF/LPF)는 ARR 유지(2), 노치만은
  ARR→1, **HPF+LPF 조합(노치 유무 무관)은 ARR→3**. 노치 Q=5~40 모두 ARR→3(폭 무관).
  ∴ **특정 필터가 아니라 표준 대역통과 필터링의 누적 효과**가 원인이며, record 105 ARR이
  분류기에서 취약 사례. **모든 AFE-측 수정(노치 제거/Q조정)으로 해결 불가**.
  (팀원 RTL ARR 점수여유 score_arr 62704 vs score_aff 33899를 뒤집음. 입력이 이미 디지털화된
  .mem이라 원본 raw 단일패스 검증은 불가.)

### 의의·권장 (최종)
- 통합 검증이 **실질적 발견**을 잡아냄: SNN 분류기가 **필터링되지 않은 원본 1kSPS .mem**으로
  튜닝되어, 표준 ECG 대역통과 필터링을 거친 신호에서 취약 사례(record 105 ARR)가 오분류.
  각 블록 단독검증으로는 못 잡는 cross-domain 이슈 → 이것이 Mixed-signal 통합 검증의 핵심 가치.
- **AFE는 스펙대로 정상**(HPF/노치/LPF 모두 IEC 요구). AFE-측 수정(노치 제거, Q 조정)으로는
  해결 불가함을 전수 실험으로 확인.
- **유일한 정답: 분류기를 필터링된(=AFE 처리) 신호로 재학습/재튜닝** (알고리즘팀 영역).
  → 본 검증의 `scripts/filter_mem.py`(AFE 등가 디지털 필터, full 모드)를 팀원 학습 데이터셋
    전체에 적용해 재학습하면 됨. 이 필터가 AFE 효과를 정확히 재현함을 입증함(digref full==AFE통합).
- 재현: `bash scripts/run_mixed_all.sh 60`(AFE 통합) · `run_digref.sh 58000 2000`(기준) ·
  `run_digref_filt.sh lpf hpf notch full hpflpf`(원인 격리) · `run_qtest.sh`(노치 Q 스윕).
