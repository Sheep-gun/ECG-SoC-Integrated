# Board and IP Packaging Evidence

## 1. 핵심 요약

최종 locked Final Membrane `structural_guarded_silent_aff_1008710`는 AXI accelerator IP source에 반영되었고, IP-XACT package와 MicroBlaze full-record replay system build까지 다시 생성했다.

중요한 경계는 다음과 같다.

- AXI/IP interface와 register map은 바뀌지 않았다.
- RTL source와 locked parameter include가 바뀌었기 때문에 accelerator IP는 재패키징했다.
- locked bitstream/XSA/ELF는 새로 생성했다.
- locked 모델 기준 실제 UART full-record board replay transcript는 아직 생성하지 않았다.

## 2. IP Packaging Evidence

| Evidence | Path | Status |
|---|---|---|
| AXI accelerator RTL wrapper | `rtl/axi/snn_ecg_axi_lite_stream_top.v` | Done |
| AXI4-Lite to AXI4-Stream feeder | `rtl/axi/axi_lite_axis_sample_feeder.v` | Done |
| Accelerator IP-XACT | `ip_repo/snn_ecg_axi_accelerator/component.xml` | Regenerated |
| Accelerator xgui | `ip_repo/snn_ecg_axi_accelerator/xgui/snn_ecg_axi_accelerator_v1_0.tcl` | Present |
| Packaged locked final layer | `ip_repo/snn_ecg_axi_accelerator/src/final_membrane_layer.v` | Updated |
| Packaged locked params include | `ip_repo/snn_ecg_axi_accelerator/src/strict_recordwise_locked_params.vh` | Added |
| Feeder IP-XACT | `ip_repo/axi_lite_axis_sample_feeder/component.xml` | Regenerated |
| Feeder xgui | `ip_repo/axi_lite_axis_sample_feeder/xgui/axi_lite_axis_sample_feeder_v1_0.tcl` | Present |

## 3. Interface Status

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Top-level ports | 변경 없음 |
| AXI4-Lite register map | 변경 없음 |
| AXI4-Stream sample width | 기존 16-bit stream 유지 |
| IP-XACT address map | 변경 없음 |
| Repackage 필요 여부 | 필요, RTL source/include 갱신 때문 |

## 4. Locked Vivado Build Evidence

Pure RTL board top:

| 항목 | 값 |
|---|---:|
| LUT / FF / BRAM / DSP | 9719 / 5038 / 0 / 0 |
| WNS | 8.184 ns |
| Estimated total power | 0.099 W |
| Bitstream | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/bitstream/snn_ecg_v2_nexys_a7_top.bit` |

OOC/profile build:

| 항목 | 값 |
|---|---:|
| PROFILE_EN=1 LUT / FF / BRAM / DSP | 9905 / 5769 / 0 / 0 |
| WNS / WHS | 0.471 ns / 0.190 ns |
| `u_final` LUT / FF | 1329 / 1037 |
| Previous `rdm_level_spike -> pred_class` path | `No timing paths found` |

## 5. MicroBlaze Full-Record Replay System Build

| Artifact | Path | Status |
|---|---|---|
| Full replay bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` | Rebuilt |
| Full replay XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` | Rebuilt |
| Full replay ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` | Rebuilt |
| Full replay app source | `vitis_apps/full_record_replay/src/main.c` | Present |
| PC sender script | `tools/board_replay/send_full_record_uart.py` | Present |

System build metrics:

| 항목 | 값 |
|---|---:|
| LUT / slice_reg / BRAM / DSP | 12485 / 8480 / 16 / 3 |
| WNS / WHS | 0.294 ns / 0.055 ns |
| Timing constraints | Met |
| CDC/check_timing markers | Clean |

BRAM/DSP are system-level resources from MicroBlaze/LMB/BRAM/UART/interconnect infrastructure, not the bare accelerator core.

## 6. Board Replay Evidence Boundary

The repo contains an earlier `test_case0_nsr` full-record board transcript under `reports/board_replay/`. It is useful as proof that the MicroBlaze/UART/sample-feeder path can run a 1,800,000-sample replay, but it is not counted as the locked `structural_guarded_silent_aff_1008710` replay result.

For the locked final model, the board replay status is:

| 항목 | 상태 |
|---|---|
| Locked bitstream/XSA/ELF build | 완료 |
| Locked UART full-record replay | TODO |
| Locked transcript | 없음 |
| Locked expected-vs-board CSV | 없음 |
| Locked board PASS/FAIL | pending |

## 7. 남은 TODO

- 새 locked bitstream을 board에 program하고 full-record UART replay 수행.
- `reports/board_replay/transcripts/locked_model_full_record_replay.txt` 저장.
- `reports/board_replay/comparisons/locked_model_expected_vs_board.csv` 저장.
- non-NSR locked board replay case 추가.
- full final_test split board replay batch는 추가 검증으로 분리.
