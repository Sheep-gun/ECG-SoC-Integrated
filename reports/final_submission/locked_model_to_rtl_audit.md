# Locked Model to RTL Audit

## Summary

This audit checks whether the strict record-wise locked Final Membrane candidate is consistently visible from Python artifacts through RTL, Vivado/IP packaging, and the Vitis/MicroBlaze board replay flow.

| 항목 | 확인 결과 | 파일/경로 | 비고 |
|---|---|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` | Source of truth |
| Locked split | `seed=20260808`, final_test locked | `configs/recordwise_resplit_seed20260808/final_test_records_locked.json` | final_test not used for selection |
| Candidate hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` | `reports/final_submission/locked_params_export_summary.json` | Also written in RTL header comments |
| Python golden load | Locked JSON is loaded explicitly | `tools/recordwise/recheck_locked_model.py` | Recheck-only script, no search |
| Python metrics | train `61/68`, validation `32/32`, final_test `29/36`, record-majority `16/19` | `reports/final_submission/python_locked_model_metrics.json` | Matches locked artifact |
| RTL include | Generated locked params include | `rtl/strict_recordwise_locked_params.vh` | Included by `rtl/final_membrane_layer.v` |
| SV package | Generated metadata/package copy | `rtl/generated/strict_recordwise_locked_params_pkg.sv` | Human/tool reference |
| RTL final layer | Locked base + structural overlay implemented | `rtl/final_membrane_layer.v` | Interface unchanged |
| XSim locked check | final_pred mismatch `0`, final_mem mismatch `0` over final_test 36 cases | `reports/final_submission/xsim_locked_model_summary.json` | Standalone final layer XSim |
| Pure RTL Vivado build | bitstream generated, timing met | `results/final_membrane_v2_snn/vivado_snn_ecg_v2/` | Locked RTL, no XSA for this pure top |
| IP package | Accelerator IP source list includes locked header | `ip_repo/snn_ecg_axi_accelerator/component.xml` | Repackaged, interface unchanged |
| MicroBlaze full replay build | bitstream/XSA/ELF rebuilt, timing met | `results/board_replay/microblaze_full_replay/` | Locked RTL build artifact |
| Locked board UART replay | Executed for NSR/CHF/ARR/AFF one 30-minute case each | `reports/final_submission/vitis_locked_model_board_replay_summary.md` | final_pred 4/4 match, final_mem exact 2/4 |

## Boundary

Locked board replay evidence is stored under `reports/board_replay/transcripts/locked_*_uart_full_replay.txt` and compared against full-top XSim class-wise replay artifacts.
