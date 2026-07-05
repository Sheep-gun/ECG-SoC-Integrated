# Vitis Locked Model Board Replay Summary

## Status

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Bitstream/XSA/ELF | rebuilt after locked IP source update |
| Actual locked UART full-record replay | executed |
| Class-wise coverage | NSR / CHF / ARR / AFF, one 30-minute case each |
| Samples per case | 1,800,000 |
| final_pred match vs full-top XSim | 4 / 4 |
| final_mem exact match vs full-top XSim | 4 / 4 |

## Replay Artifacts

| case | transcript | comparison |
|---|---|---|
| `locked_nsr_case117` | `reports/board_replay/transcripts/locked_nsr_case117_uart_full_replay.txt` | `reports/board_replay/comparisons/locked_nsr_case117_expected_vs_board.csv` |
| `locked_chf_case91` | `reports/board_replay/transcripts/locked_chf_case91_uart_full_replay.txt` | `reports/board_replay/comparisons/locked_chf_case91_expected_vs_board.csv` |
| `locked_arr_case45` | `reports/board_replay/transcripts/locked_arr_case45_uart_full_replay.txt` | `reports/board_replay/comparisons/locked_arr_case45_expected_vs_board.csv` |
| `locked_aff_case16` | `reports/board_replay/transcripts/locked_aff_case16_uart_full_replay.txt` | `reports/board_replay/comparisons/locked_aff_case16_expected_vs_board.csv` |

## Result Boundary

All four board runs completed transport and final class checks. After the sample-valid alignment fix and one-cycle processing bubble, the rebuilt bitstream matches full-top XSim at both final_pred and final_mem levels for NSR, CHF, ARR, and AFF representative 30-minute cases.
