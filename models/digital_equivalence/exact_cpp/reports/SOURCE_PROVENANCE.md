# Exact C++ source provenance

Recorded before design implementation on 2026-07-12 (Asia/Seoul).

## Repository isolation

- Source repository history: `https://github.com/Sheep-gun/SNN-ECG-Streaming-4-Class-Classifier.git`
- Source branch at isolation: `codex/accelerator-benefit-benchmark`
- Source HEAD at isolation: `5b6f01192dd84cc02022a85449a917532c1b3dca`
- Source worktree state: dirty; it was inspected only through Git metadata and was not modified.
- Exact-C++ worktree: isolated verification worktree (local path intentionally omitted)
- Exact-C++ branch: `codex/exact-cpp-baseline`
- Exact-C++ starting HEAD: `5b6f01192dd84cc02022a85449a917532c1b3dca`
- Locked digital commit: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- `git diff c6b80de..5b6f011 -- rtl configs sim reports/final/fulltop_xsim_final_test_36 reports/final/board_replay_36_cases.csv`: empty.

The starting commit contains the committed accelerator-benefit verification infrastructure added after the locked digital commit. No locked RTL, configuration, simulation source, or final XSim artifact differs between those commits.

## Locked identity

- Model ID: `structural_guarded_silent_aff_1008710`
- Locked parameter payload SHA-256: `7a4383441d6a6b2c9d88dba253ca6809f424ce36ca0a09a2876dac3696d33c1b`
- Historical locked-configuration checkout SHA-256 recorded by the committed benchmark package: `3ed5fa3399b99cace22a5cd7821be2c598a58ef27012da11a4e213a0f4c5672d`
- Locked structural-parameter checkout SHA-256: `e0c1a649515ea50bbccc7c72d2dada9080c136e9d0e23de84dcc07f93744ae53`
- Locked final-test record artifact SHA-256: `0e49b0a1f6d8f092059f759cbd1e7e2af676a55ebccd69217214cb1d7318042b`
- 36-case input manifest SHA-256: `4965b8a098617d6138e4e56e2b45febda20706b031e9bbaa2558d874517dee72`
- Input verification: 36 present, 36 SHA-256 matches, zero missing, zero mismatches.

The repository was originally hashed from a checkout with mixed historical line endings. The integrity checker therefore distinguishes semantic source identity (locked Git commit plus parsed parameter payload) from checkout-byte identity and records both. It does not rewrite locked files.

## Relevant locked RTL checkout SHA-256

| Artifact | SHA-256 |
|---|---|
| `rtl/snn_ecg_30min_final_top.v` | `6914784a2a908569bd25b825b2de7c0c8a952d0884cc6d77261aae881a5fde0e` |
| `rtl/final_membrane_layer.v` | `8d55140eb8eb48a526162520387676905be4f093e0211001900f4258dd379f20` |
| `rtl/core/ecg_event_encoder_adaptive.v` | `ca3ff35e034883083bd8126e7334e81cd47883cad0593ccd5edd92ffb395ba5c` |
| `rtl/core/qrs_lif_detector.v` | `2ac8d57cc7adea5ca55140ee0617baea6d14d250fb353c55a64b59a265ef94f9` |
| `rtl/core/pnn_rhythm_predictor.v` | `f683da51d61c26c2b1bf363f428d198961a3a88a84f0bf32012f1977f20a220e` |
| `rtl/core/rdm_variability_neuron.v` | `657a2facd4993ad2459bf112f0078cc315bdf7033a047c182852d80cdc1febfe` |
| `rtl/core/dscr_spike_counter.v` | `0b3a23d0091253e91b32d3fdc9abe4a497dde09f41c36e2f533224649e3c066d` |
| `rtl/core/ram_peak_accumulator.v` | `67a85f417ab3f90348919ede6042fe2607c00c9279c75c25efb7cbfeee676373` |
| `rtl/core/ectopic_pair_neuron.v` | `c0e817fd72fdb61d812eb25bcb27041bdb01761f756e319d0e63d581cdf9ec25` |
| `rtl/core/qrs_maf_neuron.v` | `a5fc1dd330fb6c3845163f9a4fb027fdfc408ba93169d780e02556fbd87ca466` |
| `rtl/core/rbbb_qrs_delay_bank.v` | `59f6f8d876c079c3f672de216819954ff67b89cb83f4aa61c1b22b306532376d` |
| `rtl/core/snn_ecg_3feat_top.v` | `04d05ab8a96f74bdbbed5fa03bd3cb7d89926e0c6d8d7c3279e08e33f9f75a33` |

`class_score_neurons.v` is LF-normalized by `.gitattributes` in the dedicated worktree. Its locked Git-checkout SHA-256 is `028d82ef197636d6909c9d65b936a31097e50b9b720f24ced2111435c7c4ab99`; the committed provenance table records the historical CRLF-checkout SHA-256 `b191d35665ffd74c26a3e326257c8b88653ffbcd13f7a25feac09e9d17a81cc7`.

## Existing reference and golden artifacts

| Artifact | Dedicated-checkout SHA-256 | Role |
|---|---|---|
| `models/digital_equivalence/tools/locked_integer_inference.py` | `53f8a85539bfa859011b3f8dc5075f14ee8f93dd3118ad5a66dedc55ea43ceef` | committed cycle-explicit orchestration |
| `models/digital_equivalence/tools/snapshot_c24_rtl_exact.py` | `29389a7145dda90e4958bd28276f8b83b1c87d4aa300f5304708e70ec4074988` | committed cycle-explicit Snapshot front end |
| `reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` | `3c2312416b39474053a0cd4bde5f7fe9c2c9f4d81777c169f8c78107c2e0b757` | locked full-top XSim final outputs |
| `reports/final/board_replay_36_expected_vs_board.csv` | `f7df85731aadf2a0f1d103f06bd4561a778e46ca5c60a02c1b38f37a8e52b26b` | 36-case hardware replay equivalence |

No committed Verilator-generated model or Verilator trace artifact is present at the starting commit. Uncommitted `obj/`, `tmp/`, Python runs, Verilator outputs, and benchmark results in the source worktree are explicitly excluded from authority and were not read.
