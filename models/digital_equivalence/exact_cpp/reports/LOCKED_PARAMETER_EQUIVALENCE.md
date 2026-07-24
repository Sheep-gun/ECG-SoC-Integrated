# Locked parameter equivalence

## Identity

- Digital source commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- Model ID: `structural_guarded_silent_aff_1008710`
- Locked payload SHA-256: `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b`
- Generated header SHA-256: `1c4ceda35668b8e3d26dc225551bd63acab2a207858cbc080fe5d3089ce36de8`

`tools/generate_locked_parameters.py` is the only source of `include/locked_parameters.hpp`. It first requires an empty Git diff from the locked commit to HEAD for the locked class-score RTL, strict recordwise include, final membrane RTL, full top, and both locked JSON artifacts. It then verifies the model ID and payload hash in both JSON files.

The generator parses class-score constants and RDM lookup functions from locked RTL using the committed verification parser, parses 126 final structural constants from `strict_recordwise_locked_params.vh`, and emits 529 score constants plus grouped four-class vectors and RDM level tables. Each source blob SHA-256 is embedded in the header. Regenerating the header is byte-identical.

## Covered parameter families

- input width and cadence contract: signed 12-bit, 1 kSPS semantic rhythm tick, 60,000 samples/Snapshot, 30 Snapshots/decision, gap 2;
- adaptive event thresholds and calibration bank;
- QRS membrane, leak, threshold, and refractory duration;
- PNN 46-hypothesis centers/window;
- RDM 10..150 threshold ladder;
- ectopic early/late reference thresholds;
- DSCR filter/leak/thresholds;
- RAM window/post-hold/code behavior;
- QRS MAF and RBBB width/energy/timing thresholds;
- all local score and 64-bit C24 event/segment weights and biases;
- RBBB and irregularity gates;
- all final base rewrite, guard, rescue, veto, structural, and silent-AFF thresholds/weights;
- strict-greater/first-wins Snapshot and final WTA behavior.

## Fail-closed checks

The integrity checker regenerates the header in place and requires its SHA-256 to remain unchanged. It also checks the embedded commit/model/payload identifiers, source Git diff, input manifest, all 36 input hashes, expected final artifact hashes, canonical cadence source, and equivalence results. A parameter or locked-source change therefore fails before inference evidence is accepted.

No parameter was copied from an uncommitted worktree or tuned from final-test outcomes. Corrections made during implementation concerned RTL scheduling/alignment only and were validated exhaustively against locked XSim traces.
