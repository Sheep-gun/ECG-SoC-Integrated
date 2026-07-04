# Vivado / IP Metrics

| metric | value | source |
|---|---|---|
| board LUT | 21002 | vivado_snn_ecg_v2 summary |
| board FF | 2803 | vivado_snn_ecg_v2 summary |
| board BRAM | 0 | vivado_snn_ecg_v2 summary |
| board DSP | 0 | vivado_snn_ecg_v2 summary |
| board WNS ns | 7.873 | vivado_snn_ecg_v2 timing |
| board total power W | 0.101 | Vivado estimated power |
| AXI OOC LUT | 10773 | axi_impl_timing_10ns |
| AXI OOC FF | 6931 | axi_impl_timing_10ns |
| AXI OOC BRAM | 0 | axi_impl_timing_10ns |
| AXI OOC DSP | 0 | axi_impl_timing_10ns |
| AXI OOC WNS ns | 0.081 | 10 ns post-route |
| MicroBlaze smoke LUT | 12650 | microblaze_smoke_summary |
| MicroBlaze smoke FF | 8746 | microblaze_smoke_summary |
| MicroBlaze smoke BRAM | 16 | system infrastructure included |
| MicroBlaze smoke DSP | 3 | system infrastructure included |
| MicroBlaze smoke WNS ns | 0.185 | system_timing_summary |
| MicroBlaze full replay LUT | 12638 | microblaze_full_replay_summary |
| MicroBlaze full replay FF | 8745 | microblaze_full_replay_summary |
| MicroBlaze full replay BRAM | 16 | system infrastructure included |
| MicroBlaze full replay DSP | 3 | system infrastructure included |
| MicroBlaze full replay WNS ns | 0.192 | microblaze_full_replay_summary |
| MicroBlaze full replay WHS ns | 0.026 | microblaze_full_replay_summary |

## IP Packaging Evidence

| evidence | status |
|---|---|
| snn_component_xml | present |
| snn_xgui | present |
| feeder_component_xml | present |
| feeder_xgui | present |

Limitations: Vivado power is an estimate. MicroBlaze system resources include CPU/LMB/BRAM/UART infrastructure and should not be compared directly with the bare accelerator core. The full replay system metrics are integration-build metrics for the MicroBlaze/UART/sample-feeder board replay flow.
