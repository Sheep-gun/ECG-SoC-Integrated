# 디지털 블록 (SNN 기반 ECG 4-Class Accelerator) 개요

> 본 문서는 디지털 담당(양건)의 저장소를 분석해 정리한 개요입니다.
> **정본(live source)**: https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier
> 임포트 스냅샷: `digital_block/` (upstream commit `91cad84`, 2026-07-06) — 상세는 `digital_block/_UPSTREAM_COMMIT.txt`

## 1. 위치와 역할
AFE+ADC(우리 담당)가 만든 **1kSPS signed 12-bit ECG stream**을 입력받아, SNN-inspired 방식으로 **NSR/CHF/ARR/AFF 4클래스**를 분류하는 RTL/IP accelerator. 파이프라인:
```
공개 digitized ECG → analog-equivalent vin(code/200000) → AFE+ADC XMODEL
   → signed 12-bit stream → 60초 Snapshot Readout → 30분 Final Membrane Readout → WTA → NSR/CHF/ARR/AFF
```
- **60초 Snapshot Readout**: 60초마다 event/rhythm/morphology/variability evidence를 spike·counter로 압축
- **30분 Final Membrane Readout**: 30개 snapshot(=30분)을 signed membrane에 누적(단순 다수결 아님, guarded/silent/rescue 로직) → 최종 class
- 정수 datapath(counter/comparator/signed accumulate), **DSP·BRAM 0** (weight memory·MAC 없음)

## 2. RTL 모듈 (21개, `digital_block/rtl/`)
**Top / Final**
- `snn_ecg_30min_final_top.v` — 30분 최종 분류 top
- `final_membrane_layer.v` — Final Membrane Readout (30 snapshot 누적 → WTA)
- `strict_recordwise_locked_params.vh` · `generated/strict_recordwise_locked_params_pkg.sv` — 잠금(locked) 파라미터

**Snapshot core (`rtl/core/`)**
- `snn_ecg_3feat_top.v` — 60초 snapshot readout top
- `snn_ecg_input_normalizer.v` — **입력 정규화** (ADC 스케일/진폭 정규화) ★ 우리 XADC vs SAR 스케일 논의와 직접 연결
- `ecg_event_encoder.v` / `ecg_event_encoder_adaptive.v` — delta/slope event 인코더(고정/적응형)
- `qrs_lif_detector.v` — QRS LIF beat 검출(R-peak)
- `pnn_rhythm_predictor.v` — pNNx rhythm 예측(직전 RR로 다음 beat 예측 검증)
- `rdm_variability_neuron.v` — RR variability(연속 RR 변화)
- `dscr_spike_counter.v` — 형태(slope sign flip) morphology
- `qrs_maf_neuron.v` — QRS 폭/에너지(MAF)
- `ram_peak_accumulator.v` — R-peak 진폭 인코딩
- `ectopic_pair_neuron.v` — ectopic RR pair(조기/지연 배열)
- `rbbb_qrs_delay_bank.v` — 넓은 QRS terminal delay(RBBB)
- `class_score_neurons.v` — class score/membrane 누적
- `abandoned_feature_stubs.v` — 미사용 feature stub

**인터페이스**
- `axi/snn_ecg_axi_lite_stream_top.v` — AXI4-Lite 제어 + AXI4-Stream 입력 top
- `axi/axi_lite_axis_sample_feeder.v` — MMIO→AXIS 샘플 피더
- `common/reset_sync.v` — reset 동기화

## 3. 최종 모델 & 결과
- **Locked model**: `structural_guarded_silent_aff_1008710` (Snapshot Readout 고정, Final Membrane만 strict record-wise train/val로 lock; test는 lock 후 1회만 평가)

| 평가 | 결과 |
|---|---|
| Train (68 records) | 61/68 = 89.71% |
| Validation (32 records) | 32/32 = 100.00% (model-selection 성능) |
| **Final test 30분 chunk (36)** | **29/36 = 80.56%** (macro F1 80.44 / bal.acc 80.56) |
| Final test record-majority (19) | 16/19 = 84.21% |
| chunk class recall | NSR 100 · CHF 66.67(최약) · ARR 77.78 · AFF 77.78 |
| record-majority class recall | NSR 100 · CHF 75 · ARR 77.78 · AFF 100 |

## 4. 하드웨어 검증
- **Pure RTL(Vivado)**: LUT 9,719 / FF 5,038 / BRAM 0 / DSP 0 / WNS 8.184ns / 추정전력 0.099W
- **MicroBlaze 풀 시스템**: LUT 12,494 / FF 8,494 / BRAM 16 / DSP 3 (CPU·interconnect·feeder·accelerator 포함)
- **XSim**: Python 잠금모델 vs RTL final-layer → final_pred/final_mem mismatch **0** (36 case, bit-accurate)
- **보드 replay(Vitis/MicroBlaze)**: final_test 36 record 전체(각 30분=1.8M샘플) → final_pred **36/36**, final_mem exact **36/36**
- IP-XACT 패키징(AXI accelerator + sample feeder)

## 5. 우리 AFE와의 연결 (통합 관점)
- 디지털 입력 = 우리 AFE+ADC 출력(1kSPS signed 12-bit). 우리가 만든 `datasets/fullrec_afe/`·`fullrec_afe_remaining/` full-record stream이 이 accelerator의 30분 관찰창/60s snapshot 입력으로 사용됨.
- `snn_ecg_input_normalizer.v` 존재 → 디지털 측에 입력 정규화 단이 있음. 향후 실 XADC 연동 시 우리 `docs/AFE_ADC_XADC_decision.md`의 스케일 정합(정준 코드밀도 249.5 codes/mV)과 이 정규화 단을 맞추면 됨.
- ADC 방향(XADC) 및 AFE 조건은 `docs/AFE_ADC_XADC_decision.md`, full-record 변환조건은 `docs/AFE_fullrecord_conversion_conditions.md` 참조.

## 6. 한계 (디지털팀 명시)
공개 digitized 데이터(raw sensor 아님) · AFE+ADC는 XMODEL/nominal(물리 PCB·silicon 아님) · post-layout·clinical 검증 없음 · Validation 100%는 model-selection 성능(일반화 상한 아님) · 보드 replay는 exact-match 검증(물리 아날로그 검증 아님).
