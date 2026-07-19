# Final Report Figure Index

| Figure | File | Used in | Description |
|---|---|---|---|
| Figure 1 | `reports/final/figures/final_system_architecture.png` | README, FINAL_REPORT, docs | Ownership-labeled system handoff to the digital accelerator validation flow; the current text flow inserts LTspice between MATLAB and XMODEL. |
| Figure 2 | `reports/final/figures/snapshot_to_final_membrane_pipeline.png` | FINAL_REPORT, SYSTEM_ARCHITECTURE | 60-second snapshot evidence accumulated into the 30-minute final membrane. |
| Figure 3 | `reports/final/figures/strict_recordwise_protocol.png` | FINAL_REPORT, STRICT_RECORDWISE_PROTOCOL | Record-wise split, validation usage, and final-test lock boundary. |
| Figure 4 | `reports/final/figures/final_result_summary.png` | README, FINAL_REPORT, docs | Train, validation, and locked final-test result separation. |
| Figure 5 | `reports/final/figures/hardware_validation_flow.png` | FINAL_REPORT, HARDWARE_VALIDATION | Golden/XSim/Vivado/IP-XACT/Vitis/board evidence chain. |
| Figure 6 | `reports/final/figures/resource_timing_summary.png` | FINAL_REPORT, HARDWARE_VALIDATION | Resource and timing summary from final metrics. |
| Figure 7 | `reports/final/figures/board_replay_pass_matrix.png` | FINAL_REPORT, HARDWARE_VALIDATION | 36-case board replay PASS matrix. |
| Figure 8 | `reports/final/figures/final_test_confusion_matrix.png` | FINAL_REPORT | Strict final_test confusion matrix. |
| Figure A-1 | `reports/final/figures/analog_validation/01_analog_afe_architecture.svg` | FINAL_REPORT, analog validation report | HPF/IA/notch/LPF/ADC path and injected non-idealities. |
| Figure A-2 | `reports/final/figures/analog_validation/03_matlab_ltspice_afe_response.png` | FINAL_REPORT, analog validation report | MATLAB-LTspice full AFE frequency-response comparison. |
| Figure A-3 | `reports/final/figures/analog_validation/04_matlab_ltspice_notch_response.png` | analog validation report | 60 Hz active Twin-T dense comparison. |
| Figure A-4 | `reports/final/figures/analog_validation/02_ltspice_xmodel_aligned_schematic.jpg` | FINAL_REPORT, analog validation report | XMODEL-aligned ±1.65 V LTspice schematic. |
| Figure A-5~A-7 | `reports/final/figures/analog_validation/05_*`~`07_*` | analog validation report | Full/zoom ADC overlays and per-sample error. |
| Figure A-8 | `reports/final/figures/analog_validation/10_xmodel_ltspice_adc_metrics.png` | FINAL_REPORT, analog validation report | XMODEL-LTspice 10,000-sample quantitative comparison. |
| Figure A-9 | `reports/final/figures/analog_validation/09_xmodel_ltspice_adc_agreement.png` | FINAL_REPORT, analog validation report | Exact and ±1/±2/±3/±5/±10 LSB coverage. |
| Figure A-10 | `reports/final/figures/analog_validation/08_xmodel_ltspice_adc_error_histogram.png` | analog validation report | ADC error distribution. |

Digital Figures 1-8 are generated from checked-in metrics, board replay CSVs, or protocol metadata. Run `python tools/make_final_report_figures.py` to regenerate them. Analog Figures A-1~A-10 are immutable teammate handoff copies; their original names and SHA-256 values are recorded in [`analog_validation/FIGURE_INDEX.md`](analog_validation/FIGURE_INDEX.md).
