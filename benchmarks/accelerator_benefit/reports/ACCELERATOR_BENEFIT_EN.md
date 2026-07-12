# SNN ECG Accelerator Benefit (EN)

This NO_BOARD study protects the locked classifier and uses the same 36 streams. Canonical RTL is cycle-derived at a verified 100 MHz and sample_gap_cycles=2: 54.012600 ms per stored 30-minute stream, 33.325557 MSamples/s, and 33325.56× the 1 kSPS input rate. In live operation, the final result still requires the 30-minute observation window.

Existing FPGA evidence is functional only: 36/36 pred and membrane matches, while classification accuracy remains 29/36. The benchmark-scoped exact Python integer clock model passed 36/36 prediction and membrane equivalence. With one process/thread, three warmups, and 10 repetitions per case, its median per-case-median kernel latency is 123621.089625 ms; the like-for-like stored-data RTL speedup is 2288.75×. The Verilator-generated exact C++ RTL translation passed 36/36 output equivalence and was measured after three warmups with 10 repetitions per case. The median of per-case median latencies is 2456.708125 ms. It is reported as an independent host scope, not as a Python substitute.

Pure RTL resources are 9719 LUT, 5038 FF, 0 BRAM, and 0 DSP. The design avoids a 2.7 MB raw full-window buffer. The 0.099 W figure is Vivado-estimated power; estimated energy (0.005347247400 J) is estimated power times cycle-derived stored-data latency, not measured board energy.

All timer-based board latency and physical board power remain PENDING_BOARD. The instrumented source, build attempt, schema, parser, launcher, and deterministic checklist are ready.
