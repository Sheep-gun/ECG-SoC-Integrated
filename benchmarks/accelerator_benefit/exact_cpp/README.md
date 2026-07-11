# Exact C++ SNN ECG baseline

This directory contains the hand-written, single-thread, transaction-level exact C++ baseline for locked model `structural_guarded_silent_aff_1008710` at digital commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`.

It is ordinary C++17 and has no inference-time dependency on Python, Verilator, XSim, Vivado, or numerical libraries. Python and XSim are used only by verification tools. The implementation does not execute a generic clock-toggle loop: `process_sample()` performs one accepted-sample transition plus the two architecturally meaningful canonical idle transitions, and `end_segment_or_flush()` performs the locked segment/readout transitions.

## Build

From a Visual Studio, MinGW, or other C++17 environment:

```text
cmake -S . -B build-debug -DCMAKE_BUILD_TYPE=Debug -DEXACT_CPP_TRACE=ON
cmake --build build-debug
cmake -S . -B build-release -DCMAKE_BUILD_TYPE=Release -DEXACT_CPP_TRACE=OFF
cmake --build build-release
```

`EXACT_CPP_TRACE=ON` retains Snapshot traces and enables verification-prefix/sample-hash options. `OFF` retains only the state required for inference and rejects those options. Both modes use the same fixed-width and transition code.

## Inference contract

```text
exact_cpp_ecg --input CASE.mem --format signed12_hex \
  --expected-samples 1800000 --output result.json
```

Formats are `signed12_hex` (exactly three hexadecimal digits, interpreted as 12-bit two's complement) and `decimal_signed` (`-2048..2047`). Blank lines and whole/inline `#` or `//` comments are ignored. Malformed, out-of-range, excess, or missing samples are errors; values are never clipped.

The JSON result includes final prediction, four final membranes, accepted/Snapshot/decision counts, model ID, locked parameter hash, and build ID.

## Verification

The committed evidence covers:

- 793,595 fixed-width checks, including exhaustive widths 1..8;
- 18 directed module/boundary microtraces;
- 240,000 accepted-sample feature-architecture hashes from locked full-top XSim across all four classes;
- all 1,080 Snapshot boundaries and their available feature/final states;
- all 36 final predictions and 144 final membrane values;
- debug/trace versus release/no-trace result identity on all 36 cases.

Run `tools/check_exact_cpp_integrity.py` for the fail-closed package audit. See the reports directory for the precise state set, cadence compression, parameter provenance, and evidence limits.

No performance measurement or CPU-versus-FPGA comparison is part of this package.
