# RTL Locked Final Membrane Update

## Applied Model

| 항목 | 값 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Base candidate | `balanced_0202881` |
| Split seed | `20260808` |
| Params hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| Source JSON | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |
| Generated include | `rtl/strict_recordwise_locked_params.vh` |

## RTL Changes

| 파일 | 변경 내용 |
|---|---|
| `rtl/final_membrane_layer.v` | Locked base SNN Final Membrane + structural guard/rescue/silent-AFF overlay 적용 |
| `rtl/strict_recordwise_locked_params.vh` | locked JSON에서 추출한 Verilog localparam source 추가 |
| `rtl/generated/strict_recordwise_locked_params_pkg.sv` | candidate/hash/parameter metadata package 추가 |
| `ip_repo/snn_ecg_axi_accelerator/src/final_membrane_layer.v` | packaged IP source copy 업데이트 |
| `ip_repo/snn_ecg_axi_accelerator/src/strict_recordwise_locked_params.vh` | packaged IP include 추가 |

## Interface Impact

| 항목 | 결과 |
|---|---|
| Top-level ports | 변경 없음 |
| AXI register map | 변경 없음 |
| `final_pred` / `final_mem_*` output format | 변경 없음 |
| IP-XACT address map | 변경 없음 |
| Repackage required | RTL source list 갱신 때문에 수행함 |

## Timing-Oriented RTL Note

The locked structural overlay increased the amount of final-readout combinational work, so the final membrane layer is split into `FM_BASE`, `FM_BASE_APPLY`, `FM_STRUCT`, and `FM_WTA` pipeline stages. The last snapshot is captured from post-update values before final WTA so `segment_done/chunk_done` and the final snapshot event can occur in the same cycle without losing the last evidence update.
