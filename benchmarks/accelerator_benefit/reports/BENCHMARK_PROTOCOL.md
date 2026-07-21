# Frozen Accelerator-Benefit Benchmark Protocol

- Mode: **BOARD_MEASURED_TIMING_AND_VIVADO_ESTIMATED_POWER**
- Starting commit: `795d3dbffc8dd3fbb45ad1f4ce39df92e3d33bdc`
- Branch: `codex/accelerator-benefit-benchmark`
- Locked model: `structural_guarded_silent_aff_1008710`
- Cases: the 36 rows in `reports/final/board_replay_36_cases.csv`
- Input: signed 12-bit, 1,800,000 samples per case
- Canonical RTL cadence: `sample_gap_cycles=2`
- Clock: 100 MHz, verified by the 10.000 ns constraints and implemented-system timing report
- CPU validity gate: timing is reportable only after current locked Python output matches canonical RTL `final_pred` and all four `final_mem` values 36/36.
- RTL scope: cycle-derived stored-data processing latency; XSim host wall time is forbidden.
- Board core/system timing: measured from 36 hardware-counter UART transcripts.
- Power: post-implementation vectorless Vivado estimate; physical board power is not measured.
- Live interpretation: a 30-minute final decision still requires a 30-minute observation window at 1 kSPS.
- No model, threshold, feature, class-weight, Snapshot, Final Membrane, RTL datapath, dataset, prediction, or metric change is permitted.
