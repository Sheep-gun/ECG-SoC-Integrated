# Vitis Locked Model Board Replay Summary

## Status

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Locked bitstream rebuilt | Yes |
| Locked XSA rebuilt | Yes |
| Locked MicroBlaze ELF rebuilt | Yes |
| Actual locked UART full-record replay | Not executed in this run |
| Locked transcript path | Not generated |
| Locked expected-vs-board CSV | Not generated |
| PASS/FAIL | Pending board UART replay |

## Rebuilt Artifacts

| 산출물 | 경로 |
|---|---|
| Bitstream | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit` |
| XSA | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa` |
| Bare-metal ELF | `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf` |
| System summary | `results/board_replay/microblaze_full_replay/microblaze_full_replay_summary.json` |

## Why It Is Pending

The locked board replay must be run with the newly generated bitstream/XSA/ELF. Existing `test_case0_nsr` transcript and comparison files are retained as earlier board integration evidence, but they are not counted as locked-model replay because their expected source is the previous XSim prediction artifact.

At the time of this update, Windows serial-port discovery only showed Bluetooth COM ports and no board USB-UART COM port, so the locked UART transfer was not executed.

## Command Template

After the board USB-UART port is visible, use the rebuilt locked bitstream/XSA/ELF and run the full-record sender/comparison flow. The transcript and comparison should be saved under:

- `reports/board_replay/transcripts/locked_model_full_record_replay.txt`
- `reports/board_replay/comparisons/locked_model_expected_vs_board.csv`
- `reports/board_replay/comparisons/locked_model_board_replay_summary.md`
