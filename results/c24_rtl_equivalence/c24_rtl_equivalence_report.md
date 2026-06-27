# C24 RTL Equivalence Report

## Summary

- Target model: SNN ECG Model Snapshot C24
- Dataset: `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/datasets/afe_output_xmodelmatch_curated_v2_50_25_25`
- Input used for RTL verification: AFE+ADC signed 60s snapshot `.mem` files
- Implementation style: feature spike -> signed class membrane accumulation -> segment_done 4-class WTA
- Python C24 global readout reproduction: train 434/480, val 219/240, test 193/240
- RTL C24 folded-spike WTA: train 434/480, val 219/240, test 193/240
- Python fixed-point vs RTL pred_class mismatch: train 0, val 0, test 0
- Vivado synthesis DSP usage: 0/240

## 1. Raw WTA vs C24 Python Readout

The previous RTL raw WTA used the existing local class membrane scores directly. On the curated AFE+ADC test split, that path produced 174/240 = 72.50%.

The selected C24 Python readout uses the same front-end feature extractor family, but adds a trained global readout over event counts, rate/binary features, raw base class score features, normalization, and bias. That readout produces test 193/240 = 80.42%.

The mismatch was therefore not an AFE+ADC input problem. The missing behavior was the C24 readout translation into RTL.

## 2. SNN-style Translation

The Python readout was not copied as a segment_done vector/matrix multiply block.

The C24 coefficients were folded into synaptic event weights and accumulated into four signed 64-bit class membranes:

```text
feature spike
-> c24_mem_nsr/chf/arr/aff += W_FEATURE_TO_CLASS
-> segment_done terminal binary/rate feature spikes are added
-> WTA over c24_mem_nsr/chf/arr/aff
-> pred_class
```

Continuous event weights are emitted for 28 event families, including PNN match/mismatch, DSCR flip/slope, RAM count/code, RDM valid/code, ectopic pair, pre-QRS, QRS MAF, QRS width/complex/energy, RBBB delay, EERG, and existing abandoned/base feature hooks.

RDM level features are handled as per-level spike weights for 15 thresholds.

Terminal binary/rate features are handled as one-shot segment_done membrane additions. There are 92 such binary feature weights. These are still represented as membrane events at segment end, not as a floating-point classifier.

## 3. Normalization and Bias Folding

For each C24 feature:

```text
z = (x - mean) / std
score += z * coef
```

was folded to:

```text
score += x * (coef / std)
bias  += -mean * coef / std
```

Then the folded values were quantized with:

```text
Q = 100000000
```

The generated RTL initial C24 membrane bias is:

```text
NSR -31470242
CHF -53294831
ARR -30853479
AFF -88781713
```

The raw/base class score contribution used by the Python readout was folded into the same membrane scale. The generated artifact records those base-score weights in `c24_folded_weights_for_rtl.json`.

## 4. Python Equivalence

Artifacts:

- `c24_global_readout_reproduce.json`
- `c24_folded_weight_equivalence.csv`
- `c24_fixed_point_equivalence.csv`
- `c24_folded_weights_for_rtl.json`

Results:

| split | global readout | float folded vs global | fixed-point vs float/spike |
|---|---:|---:|---:|
| train | 434/480 = 90.42% | 0 mismatch | 0 mismatch |
| val | 219/240 = 91.25% | 0 mismatch | 0 mismatch |
| test | 193/240 = 80.42% | 0 mismatch | 0 mismatch |

## 5. RTL XSim Equivalence

Artifacts:

- `xsim_train_result.csv`
- `xsim_val_result.csv`
- `xsim_test_result.csv`
- `python_vs_rtl_mismatch_report.csv`
- `python_vs_rtl_mismatch_summary.json`

Results:

| split | RTL correct/total | accuracy | Python fixed-point vs RTL pred_class mismatch |
|---|---:|---:|---:|
| train | 434/480 | 90.42% | 0 |
| val | 219/240 | 91.25% | 0 |
| test | 193/240 | 80.42% | 0 |

Test class breakdown:

| class | correct/total |
|---|---:|
| NSR | 50/64 |
| CHF | 56/64 |
| ARR | 34/54 |
| AFF | 53/58 |

## 6. Modified RTL

Modified files:

- `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/SNN_ECG.srcs/sources_1/new/class_score_neurons.v`
- `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/rtl/core/class_score_neurons.v`
- `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/SNN_ECG.srcs/sources_1/new/snn_ecg_3feat_top.v`
- `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/rtl/core/snn_ecg_3feat_top.v`

The two `class_score_neurons.v` copies are byte-identical after the C24 folded-spike patch.

The C24 path uses add/subtract and shift/add helper functions. The C24 readout path does not contain dynamic `*` multiplier operations.

## 7. DSP and Synthesis

Vivado synthesis command:

```text
C:/Xilinx/Vivado/2020.2/bin/vivado.bat -mode batch -source scripts/create_and_synth_model_s_restore.tcl
```

Synthesis result:

- Errors: 0
- Critical warnings: 0
- DSPs: 0/240 = 0.00%
- BRAM: 0/135 = 0.00%

Report files:

- `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/reports/synth/restore_model_s_utilization.rpt`
- `C:/Users/YangGeon/SNN_ECG_RESTORE_MODEL_S/reports/synth/model_s_rtl_synth_report.md`

## 8. Remaining Uncertainty

- This is functional XSim equivalence and synthesis-only resource confirmation. Full implementation/place-route timing with final board XDC constraints was not rerun in this C24 equivalence step.
- Q scale is intentionally large (`1e8`) to preserve exact C24 equivalence. Bit-width and Q-scale reduction are still later optimization work.
- No test-driven retuning or pruning was performed.
