# Ablation Summary

## Final Submission Status

The previous chunk-feature-dump ablation benchmark is retired for the final locked model report. It is not used as evidence for the locked strict record-wise Final Membrane `structural_guarded_silent_aff_1008710`.

Final performance evidence is limited to:

| item | result |
|---|---|
| locked train | 61/68 = 89.71% |
| locked validation | 32/32 = 100.00% |
| locked final_test chunk | 29/36 = 80.56% |
| locked final_test record-majority | 16/19 = 84.21% |
| final_test evaluation count | 1 |

## Remaining Ablation TODO

| experiment | status | notes |
|---|---|---|
| locked_snapshot_only | TODO | Recompute under the locked strict record-wise split. |
| locked_final_membrane_without_guards | TODO | Requires a new train/validation-only ablation protocol. |
| afe_off_raw_mem | TODO | Raw-converted non-AFE full-record `.mem` set is not present in the repo. |
| hpf_notch_lpf_off | TODO | Requires regenerating full-record `.mem` variants through the AFE/XMODEL conversion pipeline. |
| rtl_feature_module_synthesis_ablation | TODO | Requires separate RTL variants and synthesis runs. |

Figure note: the legacy ablation figure under `reports/award_readiness/figures/` is not a final locked-model result.
