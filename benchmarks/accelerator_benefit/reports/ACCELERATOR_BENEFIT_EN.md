# SNN ECG Accelerator Benefit (EN)

This NO_BOARD study protects the locked classifier and uses the same 36 streams. Canonical RTL is cycle-derived at a verified 100 MHz and sample_gap_cycles=2: 54.012600 ms per stored 30-minute stream, 33.325557 MSamples/s, and 33325.56× the 1 kSPS input rate. In live operation, the final result still requires the 30-minute observation window.

Existing FPGA evidence is functional only: 36/36 pred and membrane matches, while classification accuracy remains 29/36. CPU and C++ latency are not reported because the removed historical Python model is not exact to the final cadence-sensitive RTL. No invalid speedup is calculated.

Pure RTL resources are 9719 LUT, 5038 FF, 0 BRAM, and 0 DSP. The design avoids a 2.7 MB raw full-window buffer. The 0.099 W figure is Vivado-estimated power; estimated energy (0.005347247400 J) is estimated power times cycle-derived stored-data latency, not measured board energy.

All timer-based board latency and physical board power remain PENDING_BOARD. The instrumented source, build attempt, schema, parser, launcher, and deterministic checklist are ready.
