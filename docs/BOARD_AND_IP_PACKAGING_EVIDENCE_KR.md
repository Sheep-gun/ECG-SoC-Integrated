# Board and IP Packaging Evidence

## 1. 핵심 요약

최종 locked Final Membrane `structural_guarded_silent_aff_1008710`는 AXI accelerator IP source와 packaged IP에 반영되었다. AXI register map과 top-level interface는 유지했고, 내부 Final Membrane RTL과 locked parameter include만 갱신했다.

MicroBlaze full-record replay system은 새 locked IP 기준으로 bitstream/XSA/ELF를 다시 build했고, 실제 FPGA board에서 NSR/CHF/ARR/AFF 각 1건의 30분 full-record replay를 수행했다.

## 2. IP Packaging Evidence

| Evidence | Path | Status |
|---|---|---|
| AXI accelerator RTL wrapper | `rtl/axi/snn_ecg_axi_lite_stream_top.v` | Done |
| AXI4-Lite to AXI4-Stream feeder | `rtl/axi/axi_lite_axis_sample_feeder.v` | Done |
| Accelerator IP-XACT | `ip_repo/snn_ecg_axi_accelerator/component.xml` | Regenerated |
| Accelerator xgui | `ip_repo/snn_ecg_axi_accelerator/xgui/snn_ecg_axi_accelerator_v1_0.tcl` | Present |
| Packaged locked final layer | `ip_repo/snn_ecg_axi_accelerator/src/final_membrane_layer.v` | Updated |
| Packaged locked params include | `ip_repo/snn_ecg_axi_accelerator/src/strict_recordwise_locked_params.vh` | Updated |
| Feeder IP-XACT | `ip_repo/axi_lite_axis_sample_feeder/component.xml` | Regenerated |
| Feeder xgui | `ip_repo/axi_lite_axis_sample_feeder/xgui/axi_lite_axis_sample_feeder_v1_0.tcl` | Present |

## 3. Interface Status

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Top-level ports | 변경 없음 |
| AXI4-Lite register map | 변경 없음 |
| AXI4-Stream sample width | 16-bit 유지 |
| IP-XACT address map | 변경 없음 |
| Repackage 필요 여부 | 필요, RTL source/include 갱신 때문 |

## 4. Build Evidence

Pure RTL locked model build:

| 항목 | 값 |
|---|---:|
| LUT / FF / BRAM / DSP | 9719 / 5038 / 0 / 0 |
| WNS | 8.184 ns |
| Estimated total power | 0.099 W |

MicroBlaze full-record replay system:

| 항목 | 값 |
|---|---:|
| LUT / slice_reg / BRAM / DSP | 12485 / 8480 / 16 / 3 |
| WNS / WHS | 0.294 ns / 0.055 ns |
| Timing constraints | Met |
| CDC/check_timing markers | Clean |

BRAM/DSP는 MicroBlaze/LMB/BRAM/UART/interconnect infrastructure에서 발생한 system-level resource이고, bare accelerator core의 DSP/BRAM 사용량과 구분한다.

## 5. Board Replay Evidence

| 항목 | 결과 |
|---|---|
| Board target | Nexys A7 / Artix-7 |
| Locked bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| Locked XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| Locked ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| Class-wise replay | NSR / CHF / ARR / AFF 각 1건 |
| Samples per replay | 1,800,000 |
| final_pred match vs full-top XSim | 4 / 4 |
| final_mem exact match vs full-top XSim | 4 / 4 |

결과 요약:

- `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board_summary.md`
- `reports/board_replay/comparisons/locked_nsr_case117_summary.md`
- `reports/board_replay/comparisons/locked_chf_case91_summary.md`
- `reports/board_replay/comparisons/locked_arr_case45_summary.md`
- `reports/board_replay/comparisons/locked_aff_case16_summary.md`

## 6. 남은 검증 이슈

NSR/CHF/ARR/AFF 대표 4건의 30분 board replay는 full-top XSim과 final_pred/final_mem이 모두 일치한다. 남은 검증은 전체 final_test 36개 case로 board replay batch를 확장하는 것과, Vivado estimate가 아닌 board 전류/전력 실측을 확보하는 것이다.
