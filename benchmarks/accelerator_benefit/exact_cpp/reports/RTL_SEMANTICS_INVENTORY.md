# RTL semantics inventory

All rows refer to locked commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`. “Wrap” means truncation to the declared vector width. Pulses reset low each transition unless asserted. Sequential behavior uses old state and a simultaneous next-state commit.

| RTL module / state or operation | Width, signedness, reset | Update / overflow / saturation / shift | Ordering and persistence | C++ representation |
|---|---|---|---|---|
| `ecg_event_encoder_adaptive.prev_sample` | 12 signed, 0 | accepted sample; wrap bit pattern | first sample primes, no slope pulse; Snapshot reset | `int16_t`, explicit 12-bit input validation |
| `delta`, `abs_delta` | 13 signed / 13 unsigned, 0 | current minus old sample; exact at 13 bits; magnitude handles minimum explicitly | uses old `prev_sample` | `int16_t` / `uint16_t` |
| `sample_seen`, event pulses | 1 bit, 0 | accepted sample; strict `abs_delta > threshold`; no saturation | pulses visible next edge | bool old-output snapshots |
| adaptive histogram/bank/calibration | 64×16, 12×16, 16 unsigned, 0 | calibration accepted samples; 16-bit wrap; percentile/bank threshold selection | reset per Snapshot, threshold persists within Snapshot | arrays of `uint16_t`, explicit wrap |
| adaptive threshold/ready | 8 unsigned / 1, threshold 5 / 0 | set when calibration completes; no implicit promotion | selected from old accumulated bins | `uint8_t`, bool |
| `qrs_lif_detector.qrs_mem` | 12 unsigned, 0 | delayed-valid event integrate; threshold crossing clears; configured leak 0 | old refractory gates integration | `uint16_t`, masked 12-bit |
| QRS refractory | 10 unsigned, 0 | load 280 on beat, decrement to zero | expiry edge still suppresses integration by old state | `uint16_t`; directed expiry test |
| QRS beat pulse | 1, 0 | strict/equal threshold per RTL sum test | one-cycle delayed into consumers | bool |
| PNN token/age/RR | 1 / 12 / 12 unsigned, 0 | age saturates at 4095; beat captures old age interval | only `rhythm_tick` ages/evaluates; reset per Snapshot | bool, `uint16_t`, explicit saturation |
| PNN hypothesis scan | IDs 6 unsigned, errors 12, flags 1 | 46 centers `250+50*i`; minimum error, first tie | scan advances only on rhythm tick; old candidate state | `uint8_t`/`uint16_t`, next-state loop |
| PNN match/mismatch pulses | 1, 0 | compare chosen error to 125 | emitted after evaluation pipeline dependency | bool |
| RDM previous/current RR and diff | 1 + 12 unsigned, 0 | first RR primes; later absolute difference | consumes delayed RR-valid/held interval | bool, `uint16_t` |
| RDM level/code | 15-bit thermometer, 4-bit code | inclusive thresholds 10..150; code counts asserted levels | pulse state consumed on following score edge | `uint16_t`, `uint8_t` |
| ectopic reference/pattern | valid 1, pattern 2, RR 12 | old reference shifted update (`>>4`); early/late comparison | alternating early/late pair uses old pattern | bool, `uint8_t`, `uint16_t` |
| DSCR `filt_mem` | 24 signed, 0 | accepted current sample IIR; arithmetic `>>4`; signed wrap | old filter used for slope | `int32_t` with explicit 24-bit signed value |
| DSCR up/down membranes | 12 unsigned, 0 | slope magnitude integrate, leak 8, threshold 8; bounded branch subtraction | positive/negative channel and old sign determine flip | `uint16_t`, explicit branch arithmetic |
| DSCR valid/flip pulses | 1, 0 | accepted sample after first | score sees old pulse | bool |
| RAM window/peak | active 1, count 6, peak code 6 | current accepted sample amplitude code; max selection | beat/window uses old PNN window and beat | bool/`uint8_t` |
| RAM post hold | active 1, counter 7 | 80 accepted delayed samples, then emit | old counter controls expiry | bool/`uint8_t` |
| RAM code pulse | valid 1, code 6 | emits saved peak | one-cycle score visibility | bool/`uint8_t` |
| QRS-MAF prehistory | 120 strong/flip bits, energy bytes; 8/16-bit summaries | delayed accepted data shifts history; counts saturate where RTL tests `!=8'hff`; sums wrap | pre-beat snapshot uses old history | fixed arrays/counters |
| QRS-MAF window | active 1, post count 7, event positions/counts 8, energy 16 | 100-sample evaluation window; width/complex/energy computations | delayed sample/data; staged evaluation folded with dependencies retained | `QrsMafNeuron` old/next state |
| QRS-MAF references | width 8, energy 6, valid bits | initialize then adjust by arithmetic magnitude `>>3`; explicit truncation | evaluation compares saved old reference | `uint8_t` and bool |
| QRS-MAF pulses/values | pulses 1, width 8, codes 6 | threshold predicates and pre-QRS evidence | late evaluation pulses drain in idles/flush | bool/`uint8_t` |
| RBBB QRS activity | active/prev 1; age/gap/ref 8; match 9 | delayed sample activity; counters wrap; gap terminates QRS | old activity and old counters determine onset/end | `RbbbQrsDelayBank` old/next |
| RBBB evidence accumulators | counts 8/16, RDM sum 20 | threshold/rate/average predicates; declared-width wrap | Snapshot-local, reset on segment start | explicit narrow integers |
| RBBB valid/wide/terminal/like | pulses 1, values/counts 8 | inclusive timing/width predicates | late pulses drain before commit | bool/`uint8_t` |
| top ADC/QRS valid staging | sample 12 signed, valid 1 | accepted input capture | QRS/MAF/RBBB consume old held sample; DSCR/RAM current sample | `adc_frontend_d`, `qrs_sample_valid` |
| top RR-valid staging | 1 | old beat and active token | aligns captured RR to RDM/ectopic | `rdm_rr_valid_delay` |
| architectural trace counters | mostly 32 unsigned | old pulses increment; 32-bit wrap | reset every Snapshot, observed after flush | `uint32_t` explicit wrap |
| class local membranes | four 32 signed, class biases | event weights; explicit 32-bit wrap; no saturation | reset to bias at subwindow finalize | `array<int32_t,4>` + wrap helper |
| class accumulated score | four 32 signed, class biases | scaled local deltas, gate effects; explicit wrap; arithmetic `>>4` | score commit pipeline dependency retained for RBBB gate | `score_mem`, saved `rbbb_gate_score_mem` |
| C24 membranes | four 64 signed, locked initial values | event groups and 29 segment vectors; 64-bit wrap | captured event groups, segment predicates, WTA readout | `array<int64_t,4>` + unsigned-bit wrapping |
| C24 event group capture | group deltas 64, pending 1 | capture only when `!c24_readout_busy` | events on done accepted; next 35 busy ticks blocked | immediate add plus `c24_readout_busy_ticks` |
| C24 segment snapshots/counters | counts 8/16/20/22/32 as declared | simultaneous current pulse included via `_next`; wrap | segment predicates freeze at done | C++ counters/predicates before reset |
| subwindow timing | ms 10, ticks 17 | rhythm tick only; 60,000 boundary | last sample included before finalize | `uint16_t`/`uint32_t` masked |
| score scaling | signed 32 × unsigned Q4 | product represented 64, arithmetic right 4, low 32 | adjusted irregularity before commit | explicit `int64_t` product and logical sign-fill shift |
| RBBB delayed score gate | wait flags 1, saved gate flags | strict CHF-over-ARR block; score ±100,000 | evaluates before score commit lands; application pulse later | saved pre-commit array and delayed segment tick |
| C24 RBBB applied capture | 1 | qualified by `!c24_readout_busy` | status counter may increment while C24 applied weight is blocked | counter update without boundary C24 weight |
| Snapshot WTA | four 64 signed | strict `>` pair comparisons | equality selects lower class index | deterministic first-wins argmax |
| Snapshot controller | sample count 16+, Snapshot index 6 | 60,000 accepted samples, 30 commits | boundary sample goes directly RUN→SEG_DONE | `segment_samples_`, `snapshot_count_` |
| flush/readout controller | stage 5, pending bits | stage 0..28 plus delta/memory/WTA | 37 physical states; 36 completed updates visible pre-NBA | done tick + 36 explicit flush ticks |
| final prediction counts | 4×6 unsigned, 0 | increment Snapshot class, wrap at 6 bits | persists across 30 Snapshots | `array<uint8_t,4>` with 6-bit wrap |
| final evidence sums | 32 unsigned, 0 | add Snapshot counters, 32-bit wrap | persists across chunk; current Snapshot included | `uint32_t` explicit wrap |
| final base rewrites | four signed 32 derived from counts | locked guard/rescue/veto adds/subtracts, 32-bit wrap | predicates use fully accumulated old+current state | `current_membrane()` ordered additions |
| structural guards / silent AFF | boolean predicates | exact inclusive/strict comparisons from locked include | applied in RTL-defined order after base rewrites | same ordered predicates and weights |
| final WTA | four signed 32 | strict `>` | first class wins all ties | deterministic first-wins argmax |

## Persistence summary

Feature and class-score state resets at every Snapshot start. Final prediction counts and evidence sums persist across exactly 30 Snapshots and reset at a new final inference. Physical pending registers are not public C++ state unless their old/new dependency affects a later architectural value; those dependencies are represented by held inputs, saved gate score, readout-busy count, and explicit flush transitions.
