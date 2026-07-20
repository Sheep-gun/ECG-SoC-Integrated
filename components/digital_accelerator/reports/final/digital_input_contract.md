# Digital Input Contract

## 1. Contract Summary

The digital accelerator starts at the signed 12-bit ECG stream boundary. Upstream MATLAB and XMODEL repositories establish stream provenance; this repository verifies the accelerator from that stream onward.

| Item | Contract |
|---|---:|
| Input sample format | signed 12-bit ECG stream |
| Sample rate | 1 kSPS |
| Snapshot duration | 60 s |
| Samples per snapshot | 60,000 |
| Final decision duration | 30 min |
| Samples per final decision | 1,800,000 |
| Snapshots per final decision | 30 |
| Canonical board-facing full-top XSim cadence | `sample_gap_cycles=2` |
| Output classes | NSR, CHF, ARR, AF |

## 2. Canonical Cadence

The board-facing full-top XSim expected outputs are generated with:

```text
sample_gap_cycles=2
```

This cadence is part of the digital validation protocol for board replay comparison. It is not a model tuning knob. Upstream AFE-to-locked RTL integration evidence should use this cadence when comparing against this repo's board-facing expected outputs.

## 3. Validation Concepts

| Concept | Meaning | Owned by |
|---|---|---|
| Digital full-top XSim expected outputs | Locked full-top RTL produces expected `final_pred` and `final_mem` for 36 final_test cases | this repo |
| Vitis/MicroBlaze board replay vs expected outputs | MicroBlaze and sample feeder replay each 30-minute stream on FPGA and compare output with XSim expected | this repo |
| Upstream AFE-to-locked RTL integration evidence | XMODEL-generated stream is fed into locked RTL using the canonical cadence | XMODEL teammate repo |

## 4. Board Replay Evidence

| Item | Evidence |
|---|---:|
| 36-case replay status | completed |
| Samples per case | 1,800,000 |
| Snapshots per case | 30 |
| final_pred match vs expected | 36/36 |
| final_mem match vs expected | 36/36 |
| Classification result vs label | 29/36 = 80.56% |

Board replay validates the digital accelerator integration path. It does not validate physical electrode acquisition, a physical AFE PCB, ADC silicon, or clinical diagnosis behavior.

## 5. Cross-Repo Artifact Map

| Upstream or digital artifact | Expected connection |
|---|---|
| MATLAB nominal plots/reports | Explain nominal AFE intent before XMODEL verification |
| XMODEL generated signed 12-bit `.mem` streams | Must satisfy this repo's signed 12-bit, 1 kSPS input contract |
| XMODEL AFE-to-locked RTL integration transcript | Should use this repo's canonical full-top XSim cadence, `sample_gap_cycles=2` |
| `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` | Digital expected outputs for board-facing comparison |
| `reports/final/board_replay_36_expected_vs_board.csv` | Board replay comparison against digital expected outputs |
