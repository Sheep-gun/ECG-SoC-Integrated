# SNN ECG V2 Final Membrane XSim Report

Candidate: `margin_evidence_0038974`.

Structure: 30-minute ADC stream -> timer neuron emits one 60-second snapshot spike every 60000 accepted samples -> fixed Snapshot V2 -> final membrane signed current accumulation -> WTA.

| Split | Run tag | Python | XSim | Pred mismatch | Mem mismatch |
|---|---|---:|---:|---:|---:|
| train | train_first1 | 1/1 = 1.0000 | 1/1 = 1.0000 | 0 | 0 |

## XSim Profiling Summary

| Split | Avg total cycles | Cycles/sample | Busy ratio | Avg overhead cycles | Max window latency | Input wait cycles |
|---|---:|---:|---:|---:|---:|---:|
| train | 1801320.00 | 1.000733 | 1.000000 | 1320.00 | 60040 | 0 |

The row612 neuron is comparator/add-sub only:

```text
if arr_focus_pred == AFF and arr_focus_margin <= 12 and pred_count_ARR >= 3 and rdm_code_sum >= 512
   and pNN_mismatch >= 800 and ectopic_pair >= 256 and abnormal_evidence >= 256:
    final_mem_ARR += 4
    final_mem_AFF -= 16
```
