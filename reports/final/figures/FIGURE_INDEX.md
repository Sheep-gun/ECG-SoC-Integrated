# Final Report Figure Index

| Figure | File | Used in | Description |
|---|---|---|---|
| Figure 1 | `reports/final/figures/final_system_architecture.png` | README, FINAL_REPORT, docs | End-to-end AFE+ADC XMODEL to accelerator IP validation flow. |
| Figure 2 | `reports/final/figures/snapshot_to_final_membrane_pipeline.png` | FINAL_REPORT, SYSTEM_ARCHITECTURE | 60-second snapshot evidence accumulated into the 30-minute final membrane. |
| Figure 3 | `reports/final/figures/strict_recordwise_protocol.png` | FINAL_REPORT, STRICT_RECORDWISE_PROTOCOL | Record-wise split, validation usage, and final-test lock boundary. |
| Figure 4 | `reports/final/figures/final_result_summary.png` | README, FINAL_REPORT, docs | Train, validation, and locked final-test result separation. |
| Figure 5 | `reports/final/figures/hardware_validation_flow.png` | FINAL_REPORT, HARDWARE_VALIDATION | Golden/XSim/Vivado/IP-XACT/Vitis/board evidence chain. |
| Figure 6 | `reports/final/figures/resource_timing_summary.png` | FINAL_REPORT, HARDWARE_VALIDATION | Resource and timing summary from final metrics. |
| Figure 7 | `reports/final/figures/board_replay_pass_matrix.png` | FINAL_REPORT, HARDWARE_VALIDATION | 36-case board replay PASS matrix. |
| Figure 8 | `reports/final/figures/final_test_confusion_matrix.png` | FINAL_REPORT | Strict final_test confusion matrix. |

All figures are generated from checked-in metrics, board replay CSVs, or protocol metadata. Run `python tools/make_final_report_figures.py` to regenerate them.