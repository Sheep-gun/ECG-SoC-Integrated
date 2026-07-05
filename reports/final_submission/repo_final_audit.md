# Repo Final Audit

## 1. Scope

This audit summarizes the repository state after integrating the strict record-wise locked Final Membrane candidate through Python, RTL, XSim, Vivado, IP packaging, and the Vitis/MicroBlaze board replay build flow.

The project position remains:

```text
public digitized ECG records
-> analog-equivalent / PWL-equivalent vin reconstruction
-> nominal AFE+ADC XMODEL
-> signed 12-bit .mem stream
-> SNN-inspired ECG Classification Accelerator IP Core
-> Python / XSim / Vivado / IP packaging / Vitis build evidence
-> NSR / CHF / ARR / AFF classification
```

This is an engineering FPGA/VLSI prototype. It does not claim raw electrode acquisition, physical AFE PCB measurement, ADC silicon measurement, transistor-level post-layout verification, or medical diagnosis validation.

## 2. Confirmed Results

| 항목 | 확인 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Locked params hash | `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b` |
| Strict train | `61/68 = 89.71%` |
| Strict validation | `32/32 = 100.00%` |
| Strict final_test chunk | `29/36 = 80.56%` |
| Strict final_test record-majority | `16/19 = 84.21%` |
| test_evaluation_count | `1` |
| final_test used for selection/search/ChatGPT context | `false` |
| Python locked recheck | PASS, metrics match locked artifact |
| XSim locked final layer | final_pred mismatch `0`, final_mem mismatch `0` over final_test 36 cases |
| Pure RTL Vivado locked build | LUT/FF/BRAM/DSP `9719 / 5038 / 0 / 0`, WNS `8.184 ns`, power `0.099 W` |
| OOC/profile locked build | LUT/FF/BRAM/DSP `9905 / 5769 / 0 / 0`, WNS/WHS `0.471 ns / 0.190 ns` |
| Previous rdm->pred_class hotspot | `No timing paths found` in targeted timing query |
| MicroBlaze full replay system build | LUT/reg/BRAM/DSP `12485 / 8480 / 16 / 3`, WNS/WHS `0.294 ns / 0.055 ns` |
| IP packaging | accelerator IP repackaged, interface/register map unchanged |
| Locked full-record board UART replay | Class-wise NSR/CHF/ARR/AFF replay executed; final_pred 4/4 match |

## 3. Key Evidence Paths

| evidence | path |
|---|---|
| Locked records | `configs/recordwise_resplit_seed20260808/final_test_records_locked.json` |
| Locked params JSON | `configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json` |
| Python metrics | `reports/final_submission/python_locked_model_metrics.json` |
| Python predictions | `reports/final_submission/python_locked_model_predictions.csv` |
| RTL include | `rtl/strict_recordwise_locked_params.vh` |
| RTL final layer | `rtl/final_membrane_layer.v` |
| XSim locked summary | `reports/final_submission/xsim_locked_model_summary.md` |
| Vivado locked metrics | `reports/final_submission/vivado_locked_model_metrics.md` |
| IP packaging summary | `reports/final_submission/ip_packaging_locked_model_summary.md` |
| Vitis locked board replay summary | `reports/final_submission/vitis_locked_model_board_replay_summary.md` |

## 4. AFE+ADC XMODEL Boundary

| 항목 | 확인 결과 |
|---|---|
| Input scaling | `vin_v = signed_code / 200000` |
| Model chain | HPF `0.482 Hz` -> IA gain `x201` -> 60 Hz notch -> LPF `150 Hz` -> 12-bit ADC |
| Evidence figures | `reports/award_readiness/figures/` |
| Boundary | model-based mixed-signal-to-digital verification, not physical AFE/ADC measurement |

## 5. Board Replay Status

The locked model board bitstream, XSA, and MicroBlaze ELF were rebuilt:

- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf`

Locked UART full-record replay has been executed for one NSR, CHF, ARR, and AFF case. All four match full-top XSim at final_pred level; NSR/AFF also match final_mem exactly, while CHF/ARR final_mem divergence remains as a hardware replay semantics issue.

## 6. Remaining TODO

- Run locked full-record UART board replay and save transcript/comparison.
- Add non-NSR locked board replay case.
- Batch replay more final_test cases on board if time permits.
- Add board-level measured current/power if hardware setup is available.
- Regenerate AFE-off/filter-off full-record `.mem` variants for end-to-end ablation if needed.
