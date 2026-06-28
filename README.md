# SNN ECG Snapshot C24 With Record-Level Final Membrane

This repository contains the cleaned final implementation of the SNN-inspired
ECG 4-class classifier.

The current final system is:

```text
1 kSPS signed 12-bit AFE+ADC ECG stream
-> fixed Snapshot C24 RTL core
-> 60 s timer-neuron snapshot boundary
-> 30 min chunk vote membrane
-> record-level final membrane
-> NSR / CHF / ARR / AFF prediction
```

No floating point, divider, or DSP multiplier is used in the RTL final layer.
The final layer is implemented with counters, signed accumulators, threshold
logic, saturation-compatible integer arithmetic, and WTA comparison.

## Kept Dataset

The final verification dataset is:

```text
fullrec_afe_30min_annotation_valid_balanced/
```

It contains annotation-valid, record-wise holdout 30 minute AFE+ADC chunks:

| Split | NSR | CHF | ARR | AFF | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| train | 17 | 17 | 17 | 17 | 68 |
| val | 8 | 8 | 8 | 8 | 32 |
| test | 9 | 9 | 9 | 9 | 36 |

Manifest:

```text
fullrec_afe_30min_annotation_valid_balanced/annotation_valid_balanced_30min_manifest.csv
```

## Main RTL Files

```text
rtl/core/*.v
rtl/final_membrane_layer.v
rtl/record_level_final_membrane_layer.v
rtl/snn_ecg_30min_final_top.v
sim/tb_snn_ecg_30min_record_level_dataset.v
```

`rtl/final_membrane_layer.v` counts raw Snapshot C24 prediction spikes inside
one 30 minute chunk. `rtl/record_level_final_membrane_layer.v` accumulates those
chunk vote membranes across all chunks of the same record and applies the final
ARR rescue rule.

Selected record-level rule:

```text
base score = accumulated Snapshot pred counts
if accumulated ARR count >= 5:
    ARR score += 16
WTA tie order = NSR, CHF, ARR, AFF
```

## Python Equivalent And Search

Key scripts:

```text
scripts/snapshot_c24_rtl_exact.py
scripts/final_membrane_30min_recordwise_pipeline.py
scripts/search_final_membrane_30min_recordwise.py
scripts/search_final_membrane_30min_recordwise_recordlevel.py
scripts/search_final_membrane_30min_recordwise_recordlevel_strict.py
scripts/run_record_level_strict_xsim.py
```

Final selected Python results and reports are under:

```text
results/final_membrane_30min_recordwise/
```

The strict selected parameter file is:

```text
results/final_membrane_30min_recordwise/no_oracle_record_level_strict_selected_params.json
```

## Run XSim Verification

Run one split:

```powershell
python scripts/run_record_level_strict_xsim.py --split test
```

Run all splits:

```powershell
python scripts/run_record_level_strict_xsim.py --split all
```

The script streams the actual `.mem` chunks into RTL/XSim, emits final
record-level predictions, writes metrics, and compares Python predictions with
XSim predictions.

## Verified Performance

Full XSim verification results:

| Split | Correct / Total | Accuracy | Macro-F1 | Python-vs-XSim pred mismatch |
| --- | ---: | ---: | ---: | ---: |
| train | 55 / 68 | 80.88% | 80.19% | 0 |
| val | 29 / 32 | 90.62% | 90.28% | 0 |
| test | 30 / 36 | 83.33% | 83.11% | 0 |

After repository cleanup, the test split was rerun through RTL/XSim and matched
the same result:

```text
test: 30 / 36 = 83.33%
Python-vs-XSim pred mismatch: 0 / 36
```

Test confusion matrix, rows=true and columns=pred, class order
NSR/CHF/ARR/AFF:

```text
[[8, 1, 0, 0],
 [0, 6, 0, 3],
 [2, 0, 7, 0],
 [0, 0, 0, 9]]
```

## Resource Summary

Vivado 2020.2 synthesis summary for the final chain:

| Design | LUTs | FFs | DSP | BRAM |
| --- | ---: | ---: | ---: | ---: |
| final membrane chain | 163 | 157 | 0 | 0 |
| full 30 min top with record final membrane | 20,256 | 2,259 | 0 | 0 |

Adding the record-level final membrane to the 30 minute Snapshot C24 top costs
approximately:

```text
+109 LUT
+130 FF
+0 DSP
+0 BRAM
```
