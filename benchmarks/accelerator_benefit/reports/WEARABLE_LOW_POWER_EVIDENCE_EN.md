# Wearable Low-Power IP Evidence Extension

## Conclusion

The evidence now supports a functionally matched ECG accelerator's low-power potential on a 100 MHz Artix-7 implementation. It does not yet prove a wearable low-power semiconductor IP claim because target-node ASIC post-layout power and a complete wearable component budget are unavailable.

## Evidence completed now

| Item | Result | Class |
|---|---:|---|
| Real-ECG burst top Total On-Chip Power median | 0.1775 W | ESTIMATED |
| Real-ECG burst accelerator-hierarchy dynamic median | 0.0525 W | ESTIMATED |
| Real-ECG burst accelerator plus allocated FPGA static | 0.1495 W | ESTIMATED |
| Literal 100 MHz/1 kS/s top Total On-Chip Power median | 0.1660 W | ESTIMATED |
| Literal 1 kS/s accelerator-hierarchy dynamic median | 0.0450 W | ESTIMATED |
| Literal 1 kS/s accelerator plus allocated FPGA static | 0.1420 W | ESTIMATED |
| Accelerator allocated energy at 36.0129 ms | 5.3839 mJ | DERIVED |
| Accelerator dynamic energy at 36.0129 ms | 1.8907 mJ | DERIVED |
| Existing CE plus Vivado tool gating | 68.735% (2740 user + 727 tool / 5044) | ESTIMATED |
| Power-optimized burst top | 0.1775 W | ESTIMATED |
| Power-optimized 1 kS/s top | 0.1660 W | ESTIMATED |
| FPGA idle/active rail delta | not measured | NOT MEASURED |
| 55/65/28 nm ASIC post-layout | blocked by missing PDK/tools | NOT AVAILABLE |

Four class-representative full 1,800,000-sample burst SAIF traces and four literal 1 kS/s, 100-sample traces use real ECG data. Every burst capture passed locked final-prediction and four-membrane checks. RTL-to-routed SAIF coverage is approximately 12%; Vivado uses vectorless propagation for the remaining nets, so confidence remains Medium. This is workload-relevant estimation, not sign-off activity power.

## Streaming versus preloaded burst

- Streaming leaves the 100 MHz global clock active, so FPGA static and clock power dominate even at 1 kS/s.
- If a 30-minute record is burst-processed in 36.0129 ms and only the clock is gated afterward, average power is approximately 97.001 mW because FPGA static remains.
- The duty-cycled accelerator dynamic term alone is approximately 1.050 uW.
- An idealized full-power-gating upper bound is approximately 2.991 uW, but excludes retention, isolation, wake energy, switch leakage and off-state leakage, so it is not a product number.

The 85 uW MAX30001 ECG AFE is included only as an external datasheet reference. Sample memory, MCU, BLE and PMIC remain explicit stage gates until the parts and workloads are selected. Physical board power was not measured. Vivado values are **ESTIMATED** and power-times-latency values are **DERIVED**.
