# AFE XMODEL Evidence Run

- Source chunk: `C:\Users\YangGeon\SNN ECG Classifier\fullrec_afe_30min_annotation_valid_balanced\test\ARR\111\111_30min_w000.mem`
- Samples used: 10000 at 1000 Hz
- Scaling: `vin_v = signed_code / 200000`
- Chain: HPF 0.482 Hz -> gain x201 -> 60 Hz notch -> LPF 150 Hz -> 12-bit ADC

## Generated Figures

- `reports/award_readiness/figures/ablation_accuracy_bar.png`
- `reports/award_readiness/figures/adc_quantization_hist.png`
- `reports/award_readiness/figures/afe_chain_waveform.png`
- `reports/award_readiness/figures/afe_frequency_response.png`
- `reports/award_readiness/figures/afe_on_off_comparison.png`
- `reports/award_readiness/figures/afe_vin_reconstruction.png`
- `reports/award_readiness/figures/notch_60hz_effect.png`

## Limitation

These figures are generated from available signed .mem data and a documented nominal AFE model. They are model-evidence figures, not measured PCB/silicon or transistor-level XMODEL transient proof.
