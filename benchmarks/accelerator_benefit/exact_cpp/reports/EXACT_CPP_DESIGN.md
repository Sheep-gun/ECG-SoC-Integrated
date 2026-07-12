# Exact C++ design

## Scope and authority

The implementation is a hand-written C++17 transaction model of locked model `structural_guarded_silent_aff_1008710`. The semantic authority is locked commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`; the dedicated worktree starts from a later commit whose locked RTL/configuration diff is empty. `SOURCE_PROVENANCE.md` records every authoritative hash.

The committed Python cycle model is useful verification infrastructure, but Python interpreter overhead and array/parsing behavior are not a native CPU inference kernel. Verilator-generated C++ would remain an event-driven hardware simulator with generated clock and scheduling machinery. Neither is the requested hand-written native baseline.

## Architecture

The model is divided into the same architectural responsibilities as the RTL:

- `feature_blocks.cpp`: adaptive event encoder, QRS LIF, PNN rhythm predictor, RDM variability, ectopic pairs, DSCR, RAM amplitude, QRS MAF, and RBBB delay evidence.
- `snapshot_readout.cpp`: local score state, C24 event/segment weights, delayed RBBB gate, Snapshot WTA, and readout-busy capture semantics.
- `final_membrane.cpp`: 30-Snapshot accumulation, base rewrites, structural guards/rescues, silent-AFF path, final membranes, and final WTA.
- `exact_model.cpp`: accepted-sample/idle orchestration, segment boundary, physical-flush compression, trace checkpoints, and public inference API.
- `fixed_width.hpp`: explicit 1..64-bit two's-complement and unsigned arithmetic.

The public API is `reset`, `begin_segment`, `process_sample`, `end_segment_or_flush`, Snapshot/final accessors, and architectural hashes. The release hot path is single-threaded and has no SIMD, parallel case processing, approximation, floating point, or generated simulator code.

## Old/new-state ordering

Each feature transition snapshots the old object and computes a `next` object before assignment. `SnapshotFrontEnd::tick` first snapshots every inter-module pulse/value consumed on that edge, updates architectural counters/score from those old outputs, then ticks each producer. This reproduces nonblocking assignment visibility rather than progressively exposing new values during the same transition.

Intentional orchestration details verified against full-top XSim are:

- DSCR and RAM consume the current accepted sample.
- QRS, QRS-MAF, and RBBB consume the held one-cycle-delayed sample/data path.
- PNN hypothesis evaluation advances only on `rhythm_tick`; idle clocks hold the scan.
- Snapshot finalization includes the 60,000th accepted sample.
- RBBB delay gating evaluates saved pre-commit score state because its RTL control pipeline reaches the comparison before the score-commit pipeline.
- C24 event-group capture is blocked for the 35 busy clocks after `segment_done`; events on `segment_done` and the final visible flush update retain their RTL behavior.
- `POST_DONE_TICKS=37` produces 36 completed architectural flush updates at the pre-NBA commit observation point.

## Fixed-width behavior

Host signed overflow is never the arithmetic definition. Values are converted to unsigned bit patterns, explicitly masked to width, then interpreted as two's complement only for comparisons/results. Arithmetic right shift is implemented by sign fill, not by relying on the host treatment of negative signed shifts. Wrap, saturation, extension, slices, concatenation, shifts, multiplication, absolute minimum, and comparisons are explicit.

Large C24 and score operations use explicit 64- or 32-bit wrapping helpers. Narrow counters are truncated at the declared RTL width. Reference updates use explicitly unsigned magnitudes and truncation. Compiler warning flags include conversion and sign-conversion diagnostics; current debug and release builds are warning-clean.

## Scheduling removed and semantics retained

The implementation removes top-level clock toggling, simulator delta cycles, empty FSM bookkeeping, and pure valid/data staging after their dependency has been represented. It retains two semantic idle transitions between non-boundary samples, delayed pulses, age/leak/refractory progress, the segment-done transition, 36 visible flush updates, and Snapshot/final commit ordering. The detailed classification is in `CADENCE_COMPRESSION_JUSTIFICATION.md`.

Debug mode retains normalized Snapshot traces and accepted-sample checkpoints. Release mode compiles out trace-vector retention and rejects trace/prefix CLI options. Both modes execute identical inference transitions and produce identical deterministic result fields for all 36 locked inputs.

## Exactness achieved

The package qualifies as an **exact C++ baseline** under the requested terminology:

- fixed-width primitives: pass;
- directed module/boundary microtraces: 18/18;
- accepted-sample principal feature architecture: 240,000/240,000 hashes across four classes;
- Snapshot boundaries: 1,080/1,080 across every available field;
- final predictions: 36/36;
- final membranes: 144/144;
- debug/release deterministic result identity: 36/36.

Accepted-sample hashes intentionally exclude physical class-score/readout staging because that scheduling is compressed; the complete score, available feature counters, accumulated final state, and structural gates are compared at every Snapshot boundary. No unresolved output-affecting semantic difference remains.

## Toolchain

Verified on Windows with GNU C++ 6.2.0 (Xilinx MinGW), CMake 3.25, Ninja, C++17, `-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion`, Debug/trace, and Release/no-trace (`-O3` through CMake Release). The available MinGW distribution lacks `libasan` and `libubsan`; a sanitizer-enabled configuration was attempted and failed at link-time for those missing runtime libraries. Assertions, exhaustive arithmetic tests, warning-clean builds, XSim cross-model hashes, and full output identity provide the available checks. Sanitizers should be enabled with a toolchain that supplies the runtimes.

Performance measurement is explicitly absent and remains pending.
