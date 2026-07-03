# PROFILE_EN Synth Overhead

Top: `snn_ecg_30min_final_top` out-of-context, part `xc7a100tcsg324-1`, 10 ns clock.

| PROFILE_EN | LUT | FF | BRAM tile | DSP | Setup WNS ns | Hold WHS ns |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 10020 | 5300 | 0 | 0 | 0.881 | 0.19 |
| 1 | 10062 | 6008 | 0 | 0 | 0.881 | 0.19 |

Delta `PROFILE_EN=1 - PROFILE_EN=0`:

| Resource | Delta |
|---|---:|
| slice_lut | 42 |
| ff | 708 |
| bram_tile | 0 |
| dsp | 0 |

## Top LUT Hotspots

### PROFILE_EN=0

| Instance | Module | LUT | FF |
|---|---|---:|---:|
| `snn_ecg_30min_final_top` | `(top)` | 10020 | 5300 |
| `u_snapshot` | `snn_ecg_3feat_top` | 8167 | 3551 |
| `u_class` | `class_score_neurons` | 6814 | 2691 |
| `u_final` | `final_membrane_layer` | 1495 | 1340 |
| `u_qrs_maf` | `qrs_maf_neuron` | 407 | 349 |
| `(snn_ecg_30min_final_top)` | `(top)` | 358 | 409 |
| `u_event_encoder` | `ecg_event_encoder_adaptive` | 330 | 237 |
| `u_pnn` | `pnn_rhythm_predictor` | 155 | 77 |
| `u_rbbb_qrs_delay` | `rbbb_qrs_delay_bank` | 155 | 83 |
| `u_dscr` | `dscr_spike_counter` | 95 | 29 |
| `u_ectopic` | `ectopic_pair_neuron` | 69 | 16 |
| `u_ram` | `ram_peak_accumulator` | 43 | 24 |

### PROFILE_EN=1

| Instance | Module | LUT | FF |
|---|---|---:|---:|
| `snn_ecg_30min_final_top` | `(top)` | 10062 | 6008 |
| `u_snapshot` | `snn_ecg_3feat_top` | 8167 | 3551 |
| `u_class` | `class_score_neurons` | 6814 | 2691 |
| `u_final` | `final_membrane_layer` | 1495 | 1340 |
| `u_qrs_maf` | `qrs_maf_neuron` | 407 | 349 |
| `(snn_ecg_30min_final_top)` | `(top)` | 400 | 1117 |
| `u_event_encoder` | `ecg_event_encoder_adaptive` | 330 | 237 |
| `u_pnn` | `pnn_rhythm_predictor` | 155 | 77 |
| `u_rbbb_qrs_delay` | `rbbb_qrs_delay_bank` | 155 | 83 |
| `u_dscr` | `dscr_spike_counter` | 95 | 29 |
| `u_ectopic` | `ectopic_pair_neuron` | 69 | 16 |
| `u_ram` | `ram_peak_accumulator` | 43 | 24 |

