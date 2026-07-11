# Frozen Accelerator-Benefit Benchmark Protocol

- Mode: **NO_BOARD**
- Starting commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- Branch: `codex/accelerator-benefit-benchmark`
- Locked model: `structural_guarded_silent_aff_1008710`
- Cases: the 36 rows in `reports/final/board_replay_36_cases.csv`
- Input: signed 12-bit, 1,800,000 samples per case
- Canonical RTL cadence: `sample_gap_cycles=2`
- Clock: 100 MHz, verified by the 10.000 ns constraints and implemented-system timing report
- CPU validity gate: timing is reportable only after current locked Python output matches canonical RTL `final_pred` and all four `final_mem` values 36/36.
- RTL scope: cycle-derived stored-data processing latency; XSim host wall time is forbidden.
- Board timing and physical power: `PENDING_BOARD` until new hardware-timer transcripts or measurement records exist.
- Live interpretation: a 30-minute final decision still requires a 30-minute observation window at 1 kSPS.
- No model, threshold, feature, class-weight, Snapshot, Final Membrane, RTL datapath, dataset, prediction, or metric change is permitted.
