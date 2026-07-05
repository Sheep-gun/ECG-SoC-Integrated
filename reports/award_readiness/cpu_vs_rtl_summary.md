# CPU vs RTL Baseline

| implementation | time/chunk | chunks/sec | equiv samples/sec | notes |
|---|---|---|---|---|
| Python golden baseline model | 0.000025 s | 40087.25 | 72157047680.29 | Local Python final-readout inference on precomputed chunk features, 3 repeats; best=0.003288s. Not raw-sample CPU processing. |
| RTL cycle model @ 1 MHz | 1.800480 s | 0.56 | 999733.40 | Derived from PROFILE_EN XSim cycle counters; not wall-clock board replay. |
| RTL cycle model @ 100 MHz | 0.018005 s | 55.54 | 99973340.44 | Derived from AXI OOC 10 ns timing feasibility and cycle counters. |

- Python baseline accuracy over all chunks: 125/136 = 91.91%
- RTL cycles/sample total: 1.000267
- Energy/sample status: Vivado-estimated @1MHz: approximately 99 nJ/sample using 0.099 W total on-chip power.

Limitation: Python timing is final-readout inference on precomputed feature dumps. It is not an end-to-end CPU ECG sample-processing baseline. RTL throughput is derived from counters and Vivado reports, not a board-level full replay measurement.
