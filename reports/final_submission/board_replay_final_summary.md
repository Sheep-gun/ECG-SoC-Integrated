# Board Replay Final Summary

## Locked Model Board Replay

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Locked bitstream/XSA/ELF | Rebuilt |
| Locked full-record UART replay | Executed |
| Class coverage | NSR / CHF / ARR / AFF, one 30-minute case each |
| final_pred match vs full-top XSim | 4 / 4 |
| final_mem exact match vs full-top XSim | 2 / 4 |

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

NSR and AFF match full-top XSim at both final_pred and final_mem levels. CHF and ARR match final_pred and all transport counters, but final_mem vectors differ. The remaining technical item is sample-gap sensitivity between back-to-back direct XSim and UART/MMIO board replay.
