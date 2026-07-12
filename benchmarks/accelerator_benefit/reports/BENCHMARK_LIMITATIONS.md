# Benchmark Limitations

- No physical board was available; board timing and physical power are pending.
- Python timing is a cycle-explicit reference-model measurement and includes the canonical two idle cycles per accepted sample; it is not an optimized vectorized CPU implementation.
- Python-to-RTL speedup compares aligned stored-data processing scopes; live observation still takes 30 minutes.
- The native Exact C++ baseline is a hand-written transaction-level implementation with formally audited cadence compression; it is not a literal event-driven RTL simulation.
- Its 32.912687x FPGA-core estimate combines measured CPU latency with cycle-derived accelerator-core latency and is not measured board speedup.
- The separately reported Verilator host runtime is RTL simulation/verification evidence, not an Exact C++ or optimized CPU inference baseline; no CPU-baseline speedup is assigned to it.
- The raw Vivado power report is not committed; 0.099 W is traceable only through the locked final metrics/report summary.
- Total FF is only an all-state upper bound, not exact persistent inference memory.
- Pure RTL and complete MicroBlaze resource scopes are not directly equivalent.
- Existing UART transcripts are functional evidence, not a timer-based latency study.
- Incompatible board/host timing scopes are never combined.
