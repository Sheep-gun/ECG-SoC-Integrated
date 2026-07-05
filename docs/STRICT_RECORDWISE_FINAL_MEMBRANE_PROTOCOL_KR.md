# Strict Record-wise Final Membrane Selection Protocol

## 1. 목적

이 문서는 최종 30분 Final Membrane readout을 strict record-wise dataset 위에서 확정한 절차와 결과만 정리한다. 최종 보고서에는 채택된 구조, locked parameter, 최종 test result만 남긴다.

## 2. 고정된 입력 조건

| 항목 | 값 |
|---|---|
| Dataset split | `seed=20260808` strict record-wise split |
| Split artifact | `reports/strict_recordwise_resplit_seed20260808/strict_recordwise_split.csv` |
| Config artifact | `configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json` |
| Train / validation / test chunks | class별 17 / 8 / 9 |
| Overlap rule | `source_record_id`, `physical_record_id` 모두 split 간 overlap 0 |
| Snapshot frontend | 고정 |
| Search target | 30분 Final Membrane readout |

## 3. Final Membrane 후보 구조

후보는 단순 majority vote가 아니라 SNN-inspired final membrane 구조여야 한다. 30개의 60초 snapshot에서 발생한 class spike와 rhythm / morphology / QRS / ectopic evidence를 class neuron membrane에 흥분성 또는 억제성 current로 누적하고, 30분 window 끝에서 WTA로 NSR / CHF / ARR / AFF를 결정한다.

허용되는 연산은 RTL 이식성을 고려해 integer add/sub, shift, compare, threshold, WTA로 제한한다. multiplier-heavy ML classifier, floating point, external memory 기반 weight table은 사용하지 않는다.

## 4. 선택 절차

1. Train split에서 수백만 개 규모의 integer parameter candidate를 빠르게 평가한다.
2. ChatGPT 5.5 Pro 구조 제안을 참고하되, final_test record/result는 전달하지 않는다.
3. Validation split에서 최종 후보를 선택한다.
4. 선택된 parameter, split hash, train/validation/test record hash를 lock file로 저장한다.
5. Test split은 lock 이후 최종 1회만 평가한다.
6. 최종보고서에는 locked candidate와 final test result만 기재한다.

## 5. 최종 Locked Result

| 항목 | 결과 |
|---|---:|
| Selected candidate | `structural_guarded_silent_aff_1008710` |
| Candidate family | `F1_F6_F10_guarded_rescue_silent_aff` |
| Candidates evaluated | 3,000,000 |
| Passing candidates | 6,569 |
| Train | 61/68 = 89.71% |
| Validation | 32/32 = 100.00% |
| Final test evaluation count | 1 |
| Final test chunk accuracy | 29/36 = 80.56% |
| Final test macro-F1 | 80.44% |
| Final test record-majority accuracy | 16/19 = 84.21% |

## 6. 보고 기준

최종보고서에는 다음 항목만 남긴다.

| 항목 | 문서화 여부 |
|---|---|
| 최종 strict split 구성 | 포함 |
| 최종 Final Membrane 구조 | 포함 |
| 최종 locked parameters | 포함 |
| 최종 test result | 포함 |
| 최종 채택 외 후보 / 비최종 split / 중간 산출물 | 제외 |

## 7. RTL/Vivado 반영 상태

| 항목 | 결과 |
|---|---|
| Python source of truth | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |
| Generated RTL include | `rtl/strict_recordwise_locked_params.vh` |
| RTL implementation | `rtl/final_membrane_layer.v` |
| Standalone Final Membrane XSim | final_test 36 cases, final_pred mismatch 0, final_mem mismatch 0 |
| Vivado locked pure RTL | LUT/FF/BRAM/DSP 9719/5038/0/0, WNS 8.184 ns |
| Vitis/MicroBlaze board flow | NSR/CHF/ARR/AFF 각 1건 30분 replay 완료, final_pred/final_mem 4/4 exact match |
