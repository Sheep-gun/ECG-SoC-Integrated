# Ablation Summary

Measured rows reuse the fixed Python golden model and existing chunk feature dumps. TODO rows identify ablations that require regenerating input data or RTL variants and are not claimed as completed.

| experiment | status | correct | accuracy | delta_vs_full | notes |
|---|---|---|---|---|---|
| full_model | Measured | 125/136 | 91.91% | +0.00 pp | Frozen final Python golden rule set. |
| arr_focus_no_margin | Measured | 124/136 | 91.18% | -0.74 pp | Final model without the last AFF->ARR margin evidence rescue. |
| base_final | Measured | 120/136 | 88.24% | -3.68 pp | Base final membrane rule set before ARR-focus post rules. |
| snapshot_majority | Measured | 103/136 | 75.74% | -16.18 pp | 30 snapshot WTA votes only; no final membrane evidence currents. |
| snapshot_mem_sum | Measured | 101/136 | 74.26% | -17.65 pp | Sum of 60s snapshot class membranes only. |
| feature_sum_zeroed | Limited | 84/136 | 61.76% | -30.15 pp | Final-layer evidence sums zeroed; does not remove snapshot RTL feature extraction. |
| afe_off_raw_mem | TODO | - | - | - | Raw-converted non-AFE full-record .mem set is not present in the repo. |
| hpf_notch_lpf_off | TODO | - | - | - | Requires regenerating full-record .mem variants through the AFE/XMODEL conversion pipeline. |
| rtl_feature_module_synthesis_ablation | TODO | - | - | - | Would require separate RTL variants and synthesis runs; not fabricated here. |

Figure: `reports/award_readiness/figures/ablation_accuracy_bar.png`
