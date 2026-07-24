# 작업공간 보존 목록

이 저장소는 최종 설계와 결과를 이해·재현하는 데 필요한 원본, 모델, project, evidence와 문서만 역할별로 보존한다.

## 핵심 설계

| 범주 | 표준 위치 | 필수성 |
|---|---|---|
| MATLAB 공칭 AFE/ADC | `design/analog/matlab/` | 전달함수와 기준 vector |
| LTspice AFE/S/H/ADC | `design/analog/ltspice/` | circuit-level model |
| SystemVerilog XMODEL | `design/analog/xmodel/` | digital handoff model |
| Pure RTL | `design/digital/rtl/` | fixed synthesizable source |
| AXI IP | `design/digital/ip_repo/` | packaging and integration |
| Python equivalent model | `models/digital_equivalence/tools/` | algorithm/reference |
| Exact C++ model | `models/digital_equivalence/exact_cpp/` | integer equivalence and CPU baseline |

## Vivado project

정식 `.xpr`은 두 개만 유지한다.

1. `vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr`
2. `vivado/microblaze/SNN_ECG_MB_FULL_REPLAY.xpr`

첫 project는 Pure RTL elaborated hierarchy용이고, 둘째는 AXI/MicroBlaze implementation과 FPGA replay용이다.

## 데이터

| 자료 | 위치 |
|---|---|
| manifest, split, checksum | `datasets/` |
| 보존 raw XMODEL outputs | `datasets/xmodel_afe_adc_outputs/` |
| PhysioNet raw data | 작업공간 `_ecg_soc_physionet/`, Git 제외 |
| generated 36-case inputs | 작업공간 `generated_rtl_fpga_test_inputs_36case/`, Git 제외 |
| private submission | 작업공간 `submission_private/`, Git 제외 |

## 결과와 이력

- 사전 feature 분석: `analysis/feature_selection/`
- timing/pipeline 개발 이력: `verification/timing_optimization/`
- FPGA implementation: `verification/fpga_implementation/`
- 통합 acceptance: `verification/xmodel_rtl_acceptance_36case/`
- raw replay audit: `verification/xmodel_rtl_e2e/`
- final figures: `figures/final_submission/`
- claims and evidence: `project_registry/`, `reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv`

## 제거 대상 원칙

다음은 최종 tree에 두지 않는다.

- 복제한 전체 upstream repository
- 임시 Vivado packaging/catalog/work project
- simulator cache와 중간 compile output
- 중복 report/figure export
- private 신청서, 서명, 연락처
- 사용자 홈 절대경로
- 재생성 가능한 대용량 raw data

삭제된 자료의 연구 이력은 최종 Git history에 두 upstream history를 병합하여 보존한다.
