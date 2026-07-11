# Benchmark Limitations

- No physical board was available; board timing and physical power are pending.
- The exact current Python/C++ integer baseline is absent; historical code failed canonical output equivalence.
- The raw Vivado power report is not committed; 0.099 W is traceable only through the locked final metrics/report summary.
- Total FF is only an all-state upper bound, not exact persistent inference memory.
- Pure RTL and complete MicroBlaze resource scopes are not directly equivalent.
- Existing UART transcripts are functional evidence, not a timer-based latency study.
- No speedup is calculated because the exact Python baseline did not pass equivalence, and incompatible timing scopes are never combined.
