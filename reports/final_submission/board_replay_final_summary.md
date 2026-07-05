# Board Replay Final Summary

## Locked Model Board Replay

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Locked bitstream/XSA/ELF | Rebuilt |
| Locked full-record UART replay | Executed |
| Class coverage | NSR / CHF / ARR / AFF, one 30-minute case each |
| final_pred match vs full-top XSim | 4 / 4 |
| final_mem exact match vs full-top XSim | 4 / 4 |

## Rebuilt Board Flow Artifacts

| artifact | path |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| MicroBlaze ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| System summary | `results/board_replay/microblaze_full_replay/microblaze_full_replay_summary.json` |

## MicroBlaze System Build Metrics

| metric | value |
|---|---:|
| LUT | 12485 |
| slice_reg | 8480 |
| FF | 8479 |
| BRAM | 16 |
| DSP | 3 |
| WNS / WHS | 0.294 ns / 0.055 ns |
| timing constraints | met |

## Exactness Boundary

NSR, CHF, ARR, and AFF representative 30-minute board runs match full-top XSim at both final_pred and final_mem levels. The remaining boundary is coverage: this is class-wise representative board replay, not a full 36-case final_test board batch.
