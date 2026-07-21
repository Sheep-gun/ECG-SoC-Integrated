# SNN ECG FPGA Board Performance and Vivado Power Report

Raw firmware/schema retain the legacy `AFF` label; report-facing medical text uses `AF`. Every result is classified as MEASURED, ESTIMATED, or DERIVED.

| Item | Result | Evidence |
|---|---:|---|
| Classification accuracy | 29/36 (80.56%) | final-test annotation, MEASURED |
| Board-Golden final prediction | 36/36 | UART replay, MEASURED |
| Board-Golden Final Membrane | 144/144 | UART replay, MEASURED |
| FPGA active-core latency median / mean / range | 36.012900 / 36.012900 / 36.012900-36.012900 ms | difference of two hardware counters, DERIVED |
| FPGA active-core cycles | 3601290 cycles, identical in 36/36 | `profile_total - profile_input_wait`, DERIVED from MEASURED counters |
| FPGA active-core throughput / 1 kSPS margin | 49982089.751172 samples/s / 49982.089751x | DERIVED |
| Exact C++ / FPGA active-core speedup | 49.362861641x | CPU MEASURED / FPGA counter-derived, DERIVED |
| UART-paced raw interval median | 187144.750920 ms | transport diagnostic, MEASURED |
| Integrated-system compute latency/speedup | Not measured | requires preloaded input and independent timer |
| Pure RTL 1 MHz power | 0.099000 W | low-frequency post-implementation vectorless Vivado, ESTIMATED; no energy derived |
| Pure RTL 100 MHz accelerator+static / hierarchy dynamic / static power | 0.149500 / 0.052500 / 0.097000 W | four-class real-ECG burst SAIF median, accelerator hierarchy plus allocated FPGA static, ESTIMATED |
| Integrated FPGA system power | 0.271000 W | post-implementation vectorless Vivado, ESTIMATED |
| Pure RTL 100 MHz total energy/decision | 0.005383928550 J | clock-matched estimated total power x counter-derived latency, DERIVED ESTIMATE |
| Pure RTL 100 MHz active dynamic energy/decision | 0.001890677250 J | clock-matched estimated dynamic power x counter-derived latency, DERIVED ESTIMATE |
| Integrated system energy/decision | Not measured | no valid integrated compute latency |
| Physical board power | Not measured | no external power meter |

The Nexys A7-100T ran on `COM8` at 230400 baud. Active-core performance is `profile_total_cycles - profile_input_wait_cycles`. Both operands are MEASURED 100 MHz on-board hardware counters; latency, throughput, and speedup are DERIVED from their difference. The RTL increments input-wait only in RUN when the core is ready but `sample_valid` is absent. The subtraction therefore removes UART/MicroBlaze input starvation while retaining internal back-pressure, snapshot/final-decision work, and 1320 control cycles.

Although UART-paced raw intervals varied among cases, all 36 board differences were exactly 3601290 cycles. Canonical XSim independently gives `5,401,260 - 1,799,970 = 3,601,290 cycles`, a 36/36 cross-check. The former 54.0126 ms and 32.912687x values include the canonical sample gap and are not used as no-stall core performance. The corrected active-core result is 36.012900 ms and 49.362861641x versus Exact C++.

Raw `core_cycles/system_cycles` intervals are retained only as UART-paced transport diagnostics. They are not used for integrated-system speedup or energy. A valid integrated measurement requires preloading the ECG in DDR2 (or equivalent) and bracketing feeder start through final decision with an independent AXI Timer.

The retained 0.099 W result is the valid 1 MHz Pure RTL low-frequency estimate and is not combined with the 100 MHz active latency. The direct-100-MHz Pure RTL route met timing with WNS 0.035 ns and provides the clock-matched power used for energy. The former mixed-clock energy calculation is withdrawn from final performance claims.

The 1 MHz Pure RTL and integrated-system scopes remain vectorless. The reportable 100 MHz accelerator value uses four real-ECG burst SAIF traces, with approximately 12% routed-net matching and vectorless propagation for unmatched nets; confidence remains Medium. Literal 1 kS/s traces are reported separately. Physical board input power and measured accelerator energy were not obtained.
