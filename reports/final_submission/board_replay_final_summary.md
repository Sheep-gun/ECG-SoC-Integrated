# Board Replay Final Summary

## Locked Model Status

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Locked bitstream/XSA/ELF | Rebuilt |
| Locked full-record UART replay | Pending |
| Locked transcript | Not generated |
| Locked expected-vs-board comparison | Not generated |

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

## Legacy Board Transcript

The repo also contains an earlier `test_case0_nsr` board replay transcript:

- `reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt`
- `reports/board_replay/comparisons/test_case0_nsr_expected_vs_board.csv`

That transcript remains useful as board integration evidence for the existing UART/MicroBlaze/sample-feeder path, but it is not reported as the locked `structural_guarded_silent_aff_1008710` result. The locked model requires a fresh replay transcript generated after programming the newly rebuilt locked bitstream.
