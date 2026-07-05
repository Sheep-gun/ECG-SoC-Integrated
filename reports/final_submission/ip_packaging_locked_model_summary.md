# IP Packaging Locked Model Summary

| 항목 | 결과 |
|---|---|
| Locked candidate | `structural_guarded_silent_aff_1008710` |
| Interface changed | `false` |
| AXI register map changed | `false` |
| Repackage required | `true`, because RTL source/include changed |
| Accelerator component.xml | `ip_repo/snn_ecg_axi_accelerator/component.xml` |
| Accelerator xgui | `ip_repo/snn_ecg_axi_accelerator/xgui/snn_ecg_axi_accelerator_v1_0.tcl` |
| Packaged RTL source | `ip_repo/snn_ecg_axi_accelerator/src/final_membrane_layer.v` |
| Packaged locked include | `ip_repo/snn_ecg_axi_accelerator/src/strict_recordwise_locked_params.vh` |
| Sample feeder component.xml | `ip_repo/axi_lite_axis_sample_feeder/component.xml` |

## Result

The accelerator IP interface is unchanged: AXI4-Lite control/status, AXI4-Stream sample input, interrupt/status outputs, and final readback registers keep the same register map. The IP package was regenerated so the locked Final Membrane implementation and generated include are part of the IP-XACT source list.

The MicroBlaze full-record replay block design was rebuilt from the refreshed IP repository and exported as:

- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.bit`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay.xsa`
- `results/board_replay/microblaze_full_replay/snn_ecg_mb_full_replay_app.elf`
