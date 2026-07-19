# Section 4 analog-digital integration verification summary

| Item | Verification boundary | Result | Judgment | Primary evidence |
|---|---|---:|---|---|
| 3-1 XMODEL stream handoff | Compare SHA-256 of each generated signed 12-bit, 1 kSPS, 30-minute stream against the canonical replay input | 36/36 identical | PASS | `components/afe_xmodel/docs/integration_latest/afe36_sha256_bitidentity.csv` |
| 3-2 XMODEL stream to Digital RTL/XSim | Drive each stream at `sample_gap_cycles=2`; verify accepted count, Snapshot count, and decision count | 36/36 cases: 1,800,000 accepted, 30 Snapshots, 1 decision | PASS | `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv` |
| 3-3 End-to-end final state | Compare reproduced class and four Final Membranes with the canonical digital result | Prediction 36/36; membrane 36/36 | PASS | `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv` |

Interpretation: the table proves that the same XMODEL-generated ADC bytes enter RTL and that the implemented digital chain reproduces the expected final state.  It does not by itself prove clinical label accuracy or physical PCB/silicon behavior.
