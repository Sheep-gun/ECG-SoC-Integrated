# SNN ECG FPGA Board Performance and Vivado Power Report

Raw firmware/schema retain the legacy `AFF` label; report-facing medical text uses `AF`. Every result is classified as MEASURED, ESTIMATED, or DERIVED.

| Item | Result | Evidence |
|---|---:|---|
| Classification accuracy | 29/36 (80.56%) | final-test annotation, MEASURED |
| Board-Golden final prediction | 36/36 | UART replay, MEASURED |
| Board-Golden Final Membrane | 144/144 | UART replay, MEASURED |
| FPGA core latency median / mean / range | 187144.750920 / 188068.199890 / 186492.781740-191686.150980 ms | hardware counter, MEASURED |
| FPGA system latency median / mean / range | 187144.750920 / 188068.199890 / 186492.781740-191686.150980 ms | transaction counter, MEASURED |
| System throughput / 1 kSPS margin | 9618.223280 samples/s / 9.618223x | DERIVED |
| Exact C++ / FPGA core speedup | 0.009499063x | measured CPU / measured FPGA, DERIVED |
| Exact C++ / FPGA system speedup | 0.009499063x | measured CPU / measured FPGA, DERIVED |
| Pure RTL power | 0.099000 W | post-implementation vectorless Vivado, ESTIMATED |
| Integrated FPGA system power | 0.271000 W | post-implementation vectorless Vivado, ESTIMATED |
| Pure RTL energy/decision | 18.527330341 J | estimated power x measured core latency, DERIVED |
| Integrated system energy/decision | 50.716227499 J | estimated power x measured system latency, DERIVED |
| Physical board power | Not measured | no external power meter |

The Nexys A7-100T ran on `COM8` at 230400 baud. UART result printing occurs after the hardware counters stop. The immutable XSA has no independent AXI Timer, so neither counter is relabeled as host wall latency. For this workload the core and system counters recorded equal values because both stop at the final decision and UART pacing plus accelerator input-wait behavior are inside the measured interval. The previous 32.912687x figure remains explicitly identified as measured CPU divided by cycle-derived 54.0126 ms RTL latency; it is not the measured-board speedup.

The measured-board ratio of 0.009499063x is below one and therefore is not an acceleration. Equivalently, the FPGA core interval was 105.273540x longer than the Exact C++ kernel, and the system interval was 105.273540x longer. This is the immutable firmware counter scope with 230400-baud input wait, not the accelerator's no-stall compute-only performance.

Both power results are **Post-implementation vectorless Vivado power estimates** with no SAIF/VCD. Confidence is `Medium` for Pure RTL and `Medium` for the integrated system. Physical board input power and measured accelerator energy were not obtained.
