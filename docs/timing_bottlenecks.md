# SNN ECG RTL Timing Bottlenecks

Date: 2026-07-03

## Scope

This note records the profiling-driven RTL timing work for the SNN ECG 4-class classifier path. AXI IP wrapping remains out of scope.

## Original Bottleneck

- Hotspot: `rtl/core/class_score_neurons.v`
- Original OOC 10 ns path:
  - `u_snapshot/u_rdm/rdm_level_spike_reg[*]`
  - to `u_snapshot/u_class/pred_class_reg[*]`
- Original report showed roughly 90 logic levels and 52 CARRY4s.
- `class_score_neurons` was the largest hotspot at roughly 17.5k LUT.

## Changes Made

- Pipelined the C24/global readout and final class WTA so `rdm_level_spike -> pred_class` is no longer a same-cycle path.
- Preserved post-update segment snapshots by capturing `*_next` counters when `segment_done` is asserted.
- Registered C24 event, gate, segment, and decision deltas before applying them into `c24_mem_*`.
- Replaced local and C24 RDM threshold/code arithmetic with exact `rdm_level_code` lookup tables.
- Replaced RAM code multiply paths with exact `ram_amp_code` lookup tables for local and C24 score deltas.
- Deferred score finalization through snapshot, adjust, and commit stages while preserving signed constants and WTA tie-break order.
- Delayed RBBB score-gate evaluation so it still observes score after the deferred score commit.
- Pipelined QRS MAF pre-window scan using timestamp FIFO state instead of a 120-bit combinational scan.
- Reworked DSCR clear/reset arithmetic to avoid data-dependent reset-port timing paths.
- Registered PNN predictor center and changed `hyp_center` to a case lookup.
- Added a top-level snapshot prediction latch and increased post-segment flush budget to `POST_DONE_TICKS=36`.
- Split final membrane post-score margin/WTA into pairwise stages.
- Split the ARR score scale/commit path with a registered `score_scaled_*` stage and aligned RBBB gate evaluation by one extra cycle.
- Split the C24 gate pending path so raw gate events no longer feed `c24_gate_delta_pending` in the same cycle.
- Split the ARR high-irregular final-window predicate into product, compare, and final-AND stages so the pNN ratio carry chain no longer terminates at score/C24 pending registers.
- Hardened `scripts/synth_profile_overhead.py` and made it regenerate an explicit `rdm_to_pred_class_timing.rpt`.

## Current OOC Result

Latest command:

```text
python scripts\synth_profile_overhead.py
```

Latest resource/timing summary:

| PROFILE_EN | LUT | FF | Setup WNS ns | Hold WHS ns |
|---:|---:|---:|---:|---:|
| 0 | 10418 | 5011 | 0.133 | 0.190 |
| 1 | 10458 | 5719 | 0.133 | 0.190 |

PROFILE overhead:

| Resource | Delta |
|---|---:|
| LUT | +40 |
| FF | +708 |
| BRAM | 0 |
| DSP | 0 |

Largest remaining hierarchy blocks with `PROFILE_EN=0`:

| Instance | Module | LUT | FF |
|---|---|---:|---:|
| `u_class` | `class_score_neurons` | 6991 | 2428 |
| `u_final` | `final_membrane_layer` | 1606 | 1323 |
| `u_qrs_maf` | `qrs_maf_neuron` | 391 | 308 |

The original `rdm_level_spike -> pred_class` report now says:

```text
No timing paths found.
```

## Final Timing State

OOC 10 ns synth timing is met. The former thin/failing setup paths are gone:

- Former thin path: `pnn_match_win_count_reg[1]/C -> c24_gate_delta_pending_reg/D`
- Intermediate exposed path: `pnn_match_win_count_reg[1]/C -> score_finalize_arr_high_irregular_reg/D`
- Current worst path:
  - Source: `u_snapshot/u_class/c24_gate_delta_pending_reg_rep__1/C`
  - Destination: `u_snapshot/u_class/c24_mem_chf_reg[63]/D`
  - Slack: `0.133 ns`
  - Logic levels: `23`, including `17` CARRY4s

The original RDM-to-prediction path is gone, and the remaining reported setup/hold checks are met.

## Golden Checks

Latest RTL-vs-Python checks:

- `python scripts\run_final_membrane_v2_xsim.py --profile-smoke`
  - enabled: `total_cycles=102`, `run_cycles=16`, `accepted_samples=16`, `windows=2`, `decisions=1`, `max_window_latency=47`
  - disabled: all profile outputs remain `0`
- `python scripts\run_final_membrane_v2_xsim.py --split all --max-cases 2`
  - train: `pred_mismatch=0`, `mem_mismatch=0`
  - val: `pred_mismatch=0`, `mem_mismatch=0`
  - test: `pred_mismatch=0`, `mem_mismatch=0`
  - profiling: `accepted_samples=1800000`, `windows=30`, `decisions=1`, `input_wait=0`, `cycles/sample=1.000717`, `max_window_latency=60039`
- Non-NSR test case 9:
  - selected class: `CHF`
  - `pred_mismatch=0`, `mem_mismatch=0`
  - profiling: `accepted_samples=1800000`, `windows=30`, `decisions=1`, `input_wait=0`, `cycles/sample=1.000717`, `max_window_latency=60039`
