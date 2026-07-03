# SNN ECG RTL Timing Bottlenecks

Date: 2026-07-03

## Scope

This note records the profiling-driven RTL timing work for the SNN ECG 4-class classifier path and the follow-up AXI wrapper OOC timing checks.

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
- Added a top-level snapshot prediction latch and increased post-segment flush budget to `POST_DONE_TICKS=37`.
- Split final membrane post-score margin/WTA into pairwise stages.
- Split the ARR score scale/commit path with a registered `score_scaled_*` stage and aligned RBBB gate evaluation by one extra cycle.
- Split the C24 gate pending path so raw gate events no longer feed `c24_gate_delta_pending` in the same cycle.
- Split the ARR high-irregular final-window predicate into product, compare, and final-AND stages so the pNN ratio carry chain no longer terminates at score/C24 pending registers.
- Split the C24 segment/global memory update with a `c24_mem_delta_*` stage, while using a separate readout-origin pending bit so normal event deltas do not trigger extra WTA decisions.
- Split final membrane local and final WTA into pairwise stages so 4-class argmax no longer terminates at `p2_local_pred` or `final_pred_class` in one cycle.
- Staged QRS MAF final-window condition evaluation with captured width/energy references so ADC/sample energy arithmetic no longer feeds the condition outputs in one cycle.
- Added AXI4-Lite plus AXI-Stream wrapper, including canonical `AWPROT`/`ARPROT` ports, reset synchronizer, wrapper smoke test, AXI OOC constraints, and AXI post-route timing/CDC/IO reporting.
- Packaged the AXI wrapper as a Vivado IP-XACT core and verified catalog consumption/output generation.
- Hardened `scripts/synth_profile_overhead.py` and made it regenerate an explicit `rdm_to_pred_class_timing.rpt`.
- Added `scripts/impl_timing_10ns.py` for OOC synth/place/route timing at a 10 ns accelerator clock target.
- Added `scripts/impl_axi_timing_10ns.py` for AXI wrapper OOC synth/place/route timing at a 10 ns accelerator clock target.

## Current OOC Result

Latest command:

```text
python scripts\synth_profile_overhead.py
```

Latest resource/timing summary:

| PROFILE_EN | LUT | FF | Setup WNS ns | Hold WHS ns |
|---:|---:|---:|---:|---:|
| 0 | 10143 | 5332 | -0.145 | 0.190 |
| 1 | 10185 | 6040 | -0.145 | 0.190 |

PROFILE overhead:

| Resource | Delta |
|---|---:|
| LUT | +42 |
| FF | +708 |
| BRAM | 0 |
| DSP | 0 |

The synthesis-only timing estimate still exposes a DSCR path:

- Source: `u_snapshot/u_dscr/filt_mem_reg[0]/C`
- Destination: `u_snapshot/u_dscr/down_mem_reg[0]/D`
- Setup WNS: `-0.145 ns`
- Logic levels: `16`, including `10` CARRY4s

This is a pre-place estimate. The AXI wrapper post-route run below meets 10 ns with the same DSCR family as the routed worst path.

Largest remaining hierarchy blocks with `PROFILE_EN=0`:

| Instance | Module | LUT | FF |
|---|---|---:|---:|
| `u_class` | `class_score_neurons` | 6814 | 2691 |
| `u_final` | `final_membrane_layer` | 1495 | 1340 |
| `u_qrs_maf` | `qrs_maf_neuron` | 407 | 349 |

The original `rdm_level_spike -> pred_class` report now says:

```text
No timing paths found.
```

## Final Timing State

AXI wrapper OOC 10 ns place/route is met for `PROFILE_EN=1`.

Implementation command:

```text
python scripts\impl_axi_timing_10ns.py --profile-en 1
```

Implementation result:

| PROFILE_EN | Routed | Constraints met | Setup WNS ns | Setup TNS ns | Hold WHS ns | Hold THS ns | PW WNS ns |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | True | True | 0.081 | 0.0 | 0.098 | 0.0 | 3.750 |

AXI wrapper resource summary:

| LUT | FF | BRAM | DSP |
|---:|---:|---:|---:|
| 10773 | 6931 | 0 | 0 |

Constraint/CDC/IO checks:

- `check_timing`: no clock, unconstrained endpoint, no-input-delay, no-output-delay, partial-delay, multiple-clock, generated-clock, loop, or latch-loop issues.
- `report_cdc`: `All paths are Safely Timed.`
- `report_clock_interaction`: single `s_axi_aclk -> s_axi_aclk` interaction, `Clean`, WNS `0.08 ns`.
- `report_io`: 134 user IO in the OOC wrapper report; AXI OOC delay budget is `max 2.000 ns`, input `min 0.750 ns`, output `min -0.750 ns`.

The former thin/failing setup paths are gone:

- Former thin path: `pnn_match_win_count_reg[1]/C -> c24_gate_delta_pending_reg/D`
- Intermediate exposed path: `pnn_match_win_count_reg[1]/C -> score_finalize_arr_high_irregular_reg/D`
- Former post-route failing path: `u_snapshot/u_class/c24_gate_delta_pending_reg_rep__1_replica/C -> u_snapshot/u_class/c24_mem_chf_reg[63]/D`, slack `-1.255 ns`
- Former AXI-exposed path: `u_core/u_final/p2_local_nsr_reg[1]/C -> u_core/u_final/p2_local_pred_reg[0]/D`, slack `-0.261 ns`
- Former AXI-exposed path: `u_core/u_final/p4_final_chf_reg[0]/C -> u_core/u_final/final_pred_class_reg[0]/D`, slack `-0.324 ns`
- Former AXI-exposed path: `fifo_data0_reg[3]_replica/C -> u_core/u_snapshot/u_qrs_maf/qrs_eval_energy_cond_reg_reg/D`, slack `-0.083 ns`
- Current AXI post-route worst setup path:
  - Source: `u_core/u_snapshot/u_dscr/filt_mem_reg[0]/C`
  - Destination: `u_core/u_snapshot/u_dscr/down_mem_reg[3]/D`
  - Slack: `0.081 ns`
  - Logic levels: `19`, including `12` CARRY4s

The original RDM-to-prediction path is gone, and the remaining reported setup/hold checks are met.

## IP Packaging

Latest command:

```text
python scripts\package_snn_ecg_axi_ip.py
```

Vivado IP package:

- VLNV: `user.org:user:snn_ecg_axi_accelerator:1.0`
- Component XML: `ip_repo/snn_ecg_axi_accelerator/component.xml`
- Top module: `snn_ecg_axi_lite_stream_top`
- Interfaces: `s_axi`, `s_axis`, `s_axi_aclk`, `s_axi_aresetn`, `irq`
- AXI-Lite address range: `4096` bytes
- Catalog check: generated IP instance is `Up-to-date`; recommendation is `No changes required`

The OOC timing-budget XDC is not packaged into the reusable IP. It remains a local wrapper timing check so downstream block designs can own board-level clocks, IO delays, and physical constraints.

## Golden Checks

Latest RTL-vs-Python checks:

- `python scripts\run_final_membrane_v2_xsim.py --profile-smoke`
  - enabled: `total_cycles=104`, `run_cycles=16`, `accepted_samples=16`, `windows=2`, `decisions=1`, `max_window_latency=48`
  - disabled: all profile outputs remain `0`
- `python scripts\run_final_membrane_v2_xsim.py --split all --max-cases 2`
  - train: `pred_mismatch=0`, `mem_mismatch=0`
  - val: `pred_mismatch=0`, `mem_mismatch=0`
  - test: `pred_mismatch=0`, `mem_mismatch=0`
  - profiling: `accepted_samples=1800000`, `windows=30`, `decisions=1`, `input_wait=0`, `cycles/sample=1.000733`, `max_window_latency=60040`
- Non-NSR test case 9:
  - selected class: `CHF`
  - `pred_mismatch=0`, `mem_mismatch=0`
  - profiling: `accepted_samples=1800000`, `windows=30`, `decisions=1`, `input_wait=0`, `cycles/sample=1.000733`, `max_window_latency=60040`
