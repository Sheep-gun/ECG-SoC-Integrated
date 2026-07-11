# Ready for separate exact-C++ benchmark phase

Status:

`EXACT_CPP_IMPLEMENTED_AND_VERIFIED`

`PERFORMANCE_MEASUREMENT_PENDING`

This file is a handoff only. No performance value, timing run, throughput, power, energy, or CPU-versus-FPGA comparison is populated here.

## Release build

```text
cmake -S benchmarks/accelerator_benefit/exact_cpp \
  -B benchmarks/accelerator_benefit/exact_cpp/build-release \
  -DCMAKE_BUILD_TYPE=Release -DEXACT_CPP_TRACE=OFF
cmake --build benchmarks/accelerator_benefit/exact_cpp/build-release
```

Portable Release uses the compiler's CMake `Release` flags (GNU: `-O3 -DNDEBUG`). A separate later build may add `-march=native`, but the portable build must remain the comparison baseline and both builds must re-pass deterministic output identity. No SIMD, multithreading, approximation, or parallel case processing is authorized by this handoff.

Benchmark executable: `build-release/exact_cpp_ecg`. Release mode rejects trace output, accepted-sample hash, and incomplete-prefix options. Normal inference depends only on the executable and input stream.

## Locked input/output contract

- input set: the SHA-256-locked 36 cases in `benchmarks/accelerator_benefit/results/benchmark_dataset_manifest.csv`;
- 1,800,000 signed 12-bit samples per case;
- 60,000 samples/Snapshot, 30 Snapshots/decision;
- expected final fields: `reports/final/board_replay_36_cases.csv` and `results/final_equivalence.csv`;
- model/payload: `structural_guarded_silent_aff_1008710` / `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b`;
- debug/release deterministic result digests: `results/build_identity.csv`.

The kernel-only API is `ExactModel::reset`, optional explicit `begin_segment`, and repeated `process_sample(int16_t)` with final result retrieval. File parsing and JSON serialization are outside that kernel scope. A later benchmark must decide and report separately whether it times kernel-only inference or end-to-end parse+inference+serialization; it must not mix them.

## Fields the later benchmark must record

- exact commit SHA and clean worktree status;
- executable SHA-256 and build ID;
- compiler/vendor/version, CMake version, generator, complete compile/link flags;
- OS version, CPU model, physical/logical cores, clock/power policy, memory, process affinity;
- trace disabled confirmation and single-thread confirmation;
- input case IDs and verified input hashes;
- warm-up policy, repetition count, clock source, timing boundaries, outlier/statistical policy;
- output identity check after every measured run;
- whether portable or native-architecture flags were used.

## Required next steps

1. Start a separate benchmark task/commit without changing classifier or equivalence artifacts.
2. Run `tools/check_exact_cpp_integrity.py` before measurement.
3. Build Release with `EXACT_CPP_TRACE=OFF`; record binary/toolchain/environment hashes.
4. Define kernel-only and, if desired, end-to-end scopes independently.
5. Establish warm-up/repetition/statistical protocol before observing results.
6. Measure the exact C++ implementation; revalidate outputs and record raw runs.
7. Only then, in that separate task, combine with the authorized cycle-derived accelerator-core result and calculate any comparison.

Until those steps occur, benchmark values must remain absent and no speedup claim is valid.
