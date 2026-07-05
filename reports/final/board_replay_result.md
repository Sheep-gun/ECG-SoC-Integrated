# Board Replay Result

## Summary

The Vitis/MicroBlaze full-record replay flow was rebuilt for the locked model and run on the FPGA board. One 30-minute record was replayed for each class.

| Case | Class | Samples | Snapshots | final_pred | final_mem | Result |
|---|---|---:|---:|---:|---|---|
| `locked_nsr_case117` | NSR | 1,800,000 | 30 | 0 | 29/0/1/0 | PASS |
| `locked_chf_case91` | CHF | 1,800,000 | 30 | 1 | 0/29/0/1 | PASS |
| `locked_arr_case45` | ARR | 1,800,000 | 30 | 2 | 7/1/21/1 | PASS |
| `locked_aff_case16` | AFF | 1,800,000 | 30 | 3 | 0/0/0/30 | PASS |

All four cases match full-top XSim at both `final_pred` and `final_mem[4]`.

## Evidence

- Comparison CSVs: `reports/final/board_replay/locked_*_expected_vs_board.csv`
- UART transcripts: `reports/final/board_replay/locked_*_uart_full_replay.txt`
- XSim-vs-board summary CSV: `reports/final/board_replay/locked_class_cases_xsim_vs_board.csv`

## Remaining Scope

This is class-wise representative full-record board replay. A full 36-case final_test board batch and board-level current/power measurement were not performed.
