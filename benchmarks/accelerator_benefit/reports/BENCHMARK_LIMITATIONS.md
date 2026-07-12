# Benchmark Limitations

- No physical board was available; board timing and physical power are pending.
- Python timing is a cycle-explicit reference-model measurement and includes the canonical two idle cycles per accepted sample; it is not an optimized vectorized CPU implementation.
- Python-to-RTL speedup compares aligned stored-data processing scopes; live observation still takes 30 minutes.
- The measured C++ path is a Verilator-generated cycle-accurate RTL translation, not a hand-optimized CPU algorithm and not a Python substitute.
- The raw Vivado power report is not committed; 0.099 W is traceable only through the locked final metrics/report summary.
- Total FF is only an all-state upper bound, not exact persistent inference memory.
- Pure RTL and complete MicroBlaze resource scopes are not directly equivalent.
- Existing UART transcripts are functional evidence, not a timer-based latency study.
- Incompatible board/host timing scopes are never combined.
