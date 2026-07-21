# Streaming Memory Analysis

The accelerator updates state sample by sample and does not instantiate a 1,800,000-sample input buffer. Raw full-window storage would be 21,600,000 bits = 2,700,000 bytes (2.7 MB decimal).

Pure RTL uses 0 BRAM and 0 DSP. The 5,049 post-route FFs provide a conservative 5,049-bit (631.125-byte) upper bound on all sequential storage, but this is deliberately not called exact inference-state memory: it includes persistent inference state, pipeline registers, counters, control, and interface state. A per-category split is unavailable.
