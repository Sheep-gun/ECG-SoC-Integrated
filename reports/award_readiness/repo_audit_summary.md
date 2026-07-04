# Award Readiness Repo Audit Summary

## 조사 범위

현재 worktree 기준으로 디지털 RTL, XSim, Vivado, IP packaging, MicroBlaze smoke, AFE+ADC 입력 생성, dataset split 관련 파일을 확인했다. 이 문서는 대회 제출용 보강 전에 "repo에 실제로 존재하는 근거"와 "아직 TODO인 항목"을 분리하기 위한 감사 요약이다.

## 확인된 핵심 구현

| 영역 | 확인된 파일 / 산출물 | 상태 |
|---|---|---|
| 30분 top RTL | `rtl/snn_ecg_30min_final_top.v` | 존재 |
| 60초 snapshot core | `rtl/core/snn_ecg_3feat_top.v`, `rtl/core/class_score_neurons.v` | 존재 |
| final membrane | `rtl/final_membrane_layer.v` | 존재 |
| AXI wrapper | `rtl/axi/snn_ecg_axi_lite_stream_top.v` | 존재 |
| MMIO-to-AXIS feeder | `rtl/axi/axi_lite_axis_sample_feeder.v` | 존재 |
| XSim full-record runner | `scripts/run_final_membrane_v2_xsim.py` | 존재 |
| Python golden model | `scripts/search_final_membrane_v2_snn.py`, `scripts/search_final_membrane_v2_arr_focus.py` | 존재 |
| 30분 dataset | `fullrec_afe_30min_annotation_valid_balanced` | 존재 |
| Vivado board bitstream | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/bitstream/snn_ecg_v2_nexys_a7_top.bit` | 존재 |
| IP-XACT package | `ip_repo/snn_ecg_axi_accelerator/component.xml` | 존재 |
| sample feeder package | `ip_repo/axi_lite_axis_sample_feeder/component.xml` | 존재 |
| MicroBlaze smoke bit/XSA | `results/final_membrane_v2_snn/microblaze_smoke/snn_ecg_mb_smoke.bit`, `.xsa` | 존재 |
| XMODEL stimulus generator | `tools/ecg_to_xmodel_stimulus.py`, `tools/batch_make_xmodel_stimulus.py` | 존재 |

## 확인된 주요 수치

| 항목 | 값 | 출처 |
|---|---:|---|
| chunk-level Python/XSim test accuracy | 32/36 = 88.89% | `results/final_membrane_v2_snn/xsim_snn_ecg_v2_summary.json` |
| Python-vs-XSim mismatch | pred 0, mem 0 / 136 | `results/final_membrane_v2_snn/xsim_snn_ecg_v2_summary.json` |
| board LUT/FF/BRAM/DSP | 21002 / 2803 / 0 / 0 | `reports/award_readiness/vivado_metrics.md` |
| board WNS | 7.873 ns | `reports/award_readiness/vivado_metrics.md` |
| AXI OOC WNS @10ns | 0.081 ns | `reports/award_readiness/vivado_metrics.md` |
| MicroBlaze smoke WNS | 0.185 ns | `reports/award_readiness/vivado_metrics.md` |
| accepted samples per 30min chunk | 1,800,000 | `results/final_membrane_v2_snn/xsim_snn_ecg_v2_test_first1_profile.json` |
| cycles/sample total | 1.000267 | `reports/award_readiness/cpu_vs_rtl_summary.md` |

## 새로 수행한 보강 감사

| 감사 항목 | 결과 파일 | 핵심 결론 |
|---|---|---|
| dataset split audit | `reports/award_readiness/dataset_split_audit.md` | 현재 split은 chunk-level balanced이며 33개 class-record pair가 split을 가로지름 |
| record-wise regrouping | `reports/award_readiness/recordwise_eval_summary.md` | fixed-model record-wise stress-test test split 30/35 = 85.71% |
| LORO report | `reports/award_readiness/loro_eval_summary.md` | fixed-model record localization; class별 chunk recall 88.24-94.12% |
| AFE figure generation | `reports/award_readiness/afe_xmodel_evidence_summary.md` | nominal AFE evidence figure 생성, silicon/PCB 실측은 아님 |
| ablation | `reports/award_readiness/ablation_summary.md` | final membrane/evidence가 snapshot-only 대비 성능을 올림 |
| CPU/RTL baseline | `reports/award_readiness/cpu_vs_rtl_summary.md` | Python은 precomputed feature final-readout 기준, RTL은 cycle-derived 기준 |
| Vivado/IP metrics | `reports/award_readiness/vivado_metrics.md` | FPGA/IP packaging evidence 정리 |

## 부족한 항목

- strict record-wise protocol을 model search 이전에 고정한 독립 검증은 아직 없다.
- raw/AFE-off full-record `.mem` dataset이 없어 AFE on/off end-to-end accuracy ablation은 TODO이다.
- HPF/notch/LPF off dataset 재생성은 아직 수행하지 않았다.
- full 30분 board replay transcript는 아직 없다. 현재는 MicroBlaze smoke bit/XSA 및 XSDB MMIO smoke evidence이다.
- Vitis/MicroBlaze ELF + UART transcript는 toolchain 설치 후 실행할 항목이다.
- AFE+ADC evidence figure는 nominal model 기반이며 PCB/silicon/Virtuoso post-layout 검증이 아니다.
