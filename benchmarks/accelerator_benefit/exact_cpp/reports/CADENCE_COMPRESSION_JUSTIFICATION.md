# Cadence compression justification

Canonical RTL cadence is one accepted sample followed by two idle clocks before the next accepted sample (`sample_gap_cycles=2`). The last sample of a Snapshot is an exception at the controller boundary: RUN transitions directly to SEG_DONE, so it is not followed by an additional ordinary two-idle gap.

## Transition classification

| Class | Locked behavior | C++ transition | Retained evidence |
|---|---|---|---|
| A: accepted sample | Event encoder, DSCR, RAM consume current input; delayed QRS/MAF/RBBB paths consume held old data; rhythm state advances | First `SnapshotFrontEnd::tick(true,true,...)` in `process_sample` | 240,000 accepted-sample XSim hashes; microtraces |
| B: meaningful idle | Delayed feature pulses drain; QRS/MAF/RBBB held-valid clears; counters/score consume old pulses; non-rhythm state may advance | Two `tick(false,false,...)` calls for each non-boundary sample | all Snapshot/final comparisons; cadence-sensitive ARR representative |
| C: physical-only | Clock inversion, simulator scheduling, redundant valid pipes whose dependency is already captured, top FSM bookkeeping | Removed or represented by explicit old-output snapshots | dependency audit and exact boundary traces |
| D: segment flush | `segment_done` starts C24 readout; late feature pipelines drain; event-group capture is busy-gated; `POST_DONE_TICKS=37` reaches commit | One segment-done tick plus 36 completed flush ticks | readout-busy microtrace; 1,080 boundary traces |
| E: Snapshot/final | C24 segment readout, strict-greater WTA, final-layer commit and structural rewrites | Transactional Snapshot trace plus `FinalMembrane::commit` | all Snapshot scores/predictions/final states/gates |

## Removed or fused elements

| RTL element | Original role | Why it can be compressed | C++ representation |
|---|---|---|---|
| Top clock and event queue | Schedules posedges and NBA visibility | No architectural data by itself | Ordered function call; old outputs captured before producer ticks |
| RUN/input-wait FSM clocks | Waits for `sample_valid` | Only two canonical waits occur; their semantic state changes are known | Exactly two idle ticks, not a variable clock loop |
| ADC front-end staging | Holds sample for QRS/MAF/RBBB | Data dependency matters, register name does not | `adc_frontend_d` and `qrs_sample_valid` old-state snapshot |
| RR valid staging | Aligns completed beat interval with RDM/ectopic | One-edge dependency matters | `rdm_rr_valid_delay` and held `rr_interval` |
| Score event grouping pipes | Sums core/RDM/morph groups and later applies them | Algebraic grouping may be folded when capture is enabled | Immediate explicit fixed-width add; post-segment busy window retained |
| RBBB gate wait pipeline | Waits several clocks relative to score commit | Comparison observes pre-commit score, an architectural dependency | `rbbb_gate_score_mem` saved at finalization and used at segment gate |
| C24 29-stage segment selector | Adds one selected segment vector per stage | Order is additive with explicit 64-bit wrap; selected predicates are snapshotted | Segment predicates evaluated once and all selected vectors added in locked order |
| C24/WTA output pipeline | Stages strict-greater comparisons | Only final first-wins class is architectural | deterministic first-wins argmax after segment additions |
| Final-layer pipeline | Stages count accumulation, rewrites, gates, WTA | Old/new commit point and strict ordering are preserved transactionally | `FinalMembrane::commit` followed by `current_membrane`/WTA |

## Boundary subtleties

The 60,000th accepted sample performs its accepted transition and then immediately enters `end_segment_or_flush`; inserting two ordinary idles here changes late event alignment. The RTL declares 37 physical FLUSH states, but the edge leaving FLUSH lets commit logic observe pre-NBA values, yielding 36 completed updates. C++ therefore executes 36 post-done updates.

`c24_readout_busy` is false on the `segment_done` edge, true for the next 35 flush clocks (29 selector stages plus delta/memory/WTA staging), and false at the final visible update. `c24_readout_busy_ticks` models this capture qualification; it does not expose the physical pipeline through the public API.

## Proof scope

The cadence compression is verified at three complementary levels: accepted-sample persistent feature hashes for four class representatives including `ARR_mitdb_118_chunk00`; directed idle/flush/last-sample tests; and exact all-field boundary comparison at all 1,080 Snapshots. Final outputs then match for all 36 cases. No performance timing was collected.
