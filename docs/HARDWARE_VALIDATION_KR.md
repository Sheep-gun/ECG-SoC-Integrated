# Hardware Validation

## 검증 계층

| Layer | Evidence |
|---|---|
| Python locked recheck | `reports/final/final_metrics.json` |
| XSim final layer | final_test 36 cases, final_pred/final_mem mismatch 0 |
| Pure RTL Vivado | LUT/FF/BRAM/DSP 9719/5038/0/0, WNS 8.184 ns |
| OOC/profile Vivado | LUT/FF/BRAM/DSP 9905/5769/0/0, WNS 0.471 ns |
| IP packaging | accelerator/sample-feeder `component.xml`, `xgui` |
| MicroBlaze full replay build | bitstream/XSA/ELF generated |
| Board replay | class-wise 30-minute replay, final_pred/final_mem exact 4/4 |

## Board Replay

| Case | Class | Samples | Snapshot count | final_mem | Result |
|---|---|---:|---:|---|---|
| `locked_nsr_case117` | NSR | 1,800,000 | 30 | 29/0/1/0 | PASS |
| `locked_chf_case91` | CHF | 1,800,000 | 30 | 0/29/0/1 | PASS |
| `locked_arr_case45` | ARR | 1,800,000 | 30 | 7/1/21/1 | PASS |
| `locked_aff_case16` | AFF | 1,800,000 | 30 | 0/0/0/30 | PASS |

All four board runs match full-top XSim at both final class and final membrane levels.

## Key Artifacts

| Artifact | Path |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| MicroBlaze ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| Board replay result | `reports/final/board_replay_result.md` |
| Vivado metrics | `reports/final/vivado_locked_model_metrics.md` |
| XSim summary | `reports/final/xsim_locked_model_summary.md` |

## Boundary

The board replay is class-wise representative full-record replay. It is not a full 36-case final_test board batch, and it is not board-level current/power measurement.
