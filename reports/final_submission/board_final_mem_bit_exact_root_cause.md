# Board Final Membrane Bit-Exact Root Cause

## Summary

The locked class-wise board replay initially matched `final_pred` but not all `final_mem` vectors. The issue was not a model parameter mismatch. It was a replay-semantics mismatch between back-to-back full-top XSim and UART/MMIO board input pacing.

## Root Cause

`ecg_event_encoder_adaptive` emits registered event signals one clock after an accepted input sample. Several downstream feature blocks consumed those registered event pulses using the current `sample_valid` timing. Back-to-back XSim masked the problem because `sample_valid` stayed high continuously, while the UART/MMIO feeder introduced gaps between samples on board.

## RTL Fix

| file | change |
|---|---|
| `rtl/core/snn_ecg_3feat_top.v` | Added one-cycle aligned `qrs_sample_valid` and delayed frontend sample for registered event consumers. |
| `rtl/snn_ecg_30min_final_top.v` | Added a one-cycle processing bubble after accepted samples so registered event pulses are consumed before the next sample. |
| `rtl/core/pnn_rhythm_predictor.v` | Kept rhythm hypothesis scan tied to rhythm sample ticks. |
| `ip_repo/snn_ecg_axi_accelerator/src/*` | Mirrored the RTL fixes into the packaged IP source tree. |

## Verification

| check | result |
|---|---|
| full-top XSim expected values | regenerated for locked class-wise cases |
| full-top XSim vs board summary | `all_final_pred_match=True`, `all_final_mem_match=True` |
| NSR board replay | `29/0/1/0`, exact PASS |
| CHF board replay | `0/29/0/1`, exact PASS |
| ARR board replay | `7/1/21/1`, exact PASS |
| AFF board replay | `0/0/0/30`, exact PASS |

Evidence:

- `reports/final_submission/fulltop_xsim_locked_class_cases/locked_class_cases_xsim_vs_board_summary.md`
- `reports/board_replay/comparisons/locked_*_summary.md`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf`
