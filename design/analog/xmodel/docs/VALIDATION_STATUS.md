# AFE / Mixed-signal 검증 상태 (VALIDATION_STATUS)

> 제27회 반도체설계대전 · 한양대 · AFE(이수환) 담당 검증 요약 · 갱신 2026-07-09
> 각 claim은 아래 산출물로 근거 추적 가능. 공식 결과는 canonical 조건 기준만 사용.

| 항목 | 상태 | 산출물 | claim (요지) |
|---|---|---|---|
| AFE clipping / headroom | **PASS** | `docs/afe_stress/clipping_report.csv` | 분류기 입력 60s chunk 1,200개 clipping 0; full-record DB 127개 clip ratio 0.00007% |
| emu↔XModel 36세그 정합 | **PASS** | `docs/afe_stress/afe_val36_segment_list.csv` | 평균 RMS 1.95 LSB, lag 0 (QRS 첨두 sub-sample 편차만) |
| R-peak / morphology 보존 | **PASS** | `docs/afe_stress/rpeak_timing_test.csv` | 매칭 100%(중앙값), 군지연 1 ms, RR 오차 0 ms |
| 50/60Hz PLI | **PASS (scope-limited)** | `docs/afe_stress/AFE_xmodel_verification.md` | 60Hz target(잔차 0.9mV); 50Hz는 notch retune 필요(scope 밖) |
| 전극 offset / baseline wander | **PASS** | `docs/afe_stress/AFE_xmodel_verification.md` | HPF-before-gain → ±200mV offset에도 정착 후 clipping 0 |
| R/C mismatch | **PARTIAL (equivalence)** | `docs/afe_stress/AFE_xmodel_verification.md` | 0.1% CMRR 100.7dB/1% 80dB; final_pred는 equivalence-based robustness argument |
| op-amp GBW / VOS | **PASS (caveat)** | `docs/afe_stress/AFE_xmodel_verification.md` | GBW 100kHz까지 ECG 영향 ≤2 code; VOS ×201 headroom → 저오프셋/DC servo 권장 |
| ADC non-ideal final_pred | **PASS (one extreme flip)** | `docs/afe_stress/adc_nonideal_finalpred_xsim.csv` (+`_map.csv`), threshold `adc_nonideal_noise_threshold_xsim.csv/.md` | 15/16 유지; offset±5LSB/gain±1%/jitter100µs·noise≤1LSB 안정, noise 2LSB rms에서만 NSR 1건 flip |
| AFE→locked RTL integration | **PASS** | `docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv` · `afe36_sha256_bitidentity.csv` | SHA256 36/36 identical + canonical cadence(gap=2)에서 final_pred·final_membrane 36/36 bit-exact |
| physical PCB / silicon / clinical | **NOT DONE** | scope limitation | 물리 계측/silicon/임상 claim 금지 (model-based verification) |

## 검증 경계 (claim boundary)
- 공식 통합 결과는 **canonical board-facing XSim cadence(`sample_gap_cycles=2`)** 기준만 사용. fast harness(gap=0) 결과는 debug/obsolete로만 분리.
- R/C mismatch final_pred는 **직접 30분 XModel sweep이 아님** → XMODEL stress metric + ADC non-ideal final_pred regression 기반 **equivalence-based robustness argument**로 제시.
- 입력 ECG는 실제 전극 raw analog이 아니라 공개 digitized record. AFE+ADC 검증은 XMODEL/emulator 기반 model-based verification(물리 PCB/silicon 계측 아님).

## 파이프라인 (공식 요약)
```
AFE fullrec output → 30min chunk slicing (start = 2000 + chunk_id×1,800,000)
  → SHA256 36/36 identical to digital board-replay input
  → canonical board-facing XSim cadence (sample_gap_cycles = 2)로 locked full-top RTL 재실행
  → final_pred 36/36 match
  → final_membrane 36/36 bit-exact
```
