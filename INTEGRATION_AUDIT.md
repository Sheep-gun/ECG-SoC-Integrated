# Integration and publication audit

## Public baseline and local maintenance

- Public repository: `https://github.com/Sheep-gun/ECG-SoC-Integrated`
- Remote: `origin` → `https://github.com/Sheep-gun/ECG-SoC-Integrated.git`
- Branch: `main`
- Verified pre-maintenance public baseline: `32d2fbd582040f7de7ed54e4ecf5a8a4efd19268`
- Baseline message: `Add integrated Korean technical report manuscript`
- Technical manuscript: `reports/INTEGRATED_TECHNICAL_REPORT_KR.md` present and maintained
- History rewrite: local publication-readiness rewrite performed; not pushed during this task
- Post-rewrite content commit preceding final audit: `a64919be207f7131202a735bdc2def93d198ab56`
- Actual final local HEAD: report with `git rev-parse HEAD`; a committed file does not claim its own SHA

## Curated component provenance

| Component | Fixed commit | Owner | Policy |
|---|---|---|---|
| MATLAB nominal pre-validation | `907f7e1f081a9d6a5703a32095d962143315a192` | 서민우 | retained files byte-identical to fixed Git objects |
| AFE+ADC XMODEL | `4756a5086023547328ef44fd5fd87da3c250dc39` | 이수환 | retained files byte-identical; raw PhysioNet/submission/temp paths registered and omitted |
| Digital accelerator | `c6b80de19cdcad5b7e43fe7835588b629d847f75` | 양건 | retained files byte-identical to fixed Git objects |
| Digital benchmark evidence | `09e4d840827ad20856f5e23be4743ddd01565e30` | 양건 | curated NO_BOARD reports/results; locked digital authority remains `c6b80de` |
| XMODEL-aligned LTspice validation handoff | `INTEGRATED_LTSPICE_2026-07-19` | 이수환 | graphical schematic/netlist/model, compact vectors, 35-run tables/logs and ten immutable figures; multi-GB raw waveforms omitted |

The repository is a curated technical snapshot, not a complete mirror of every upstream tracked path. Fixed upstream commits remain the authoritative complete snapshots. `artifact_manifest.csv` covers all retained files; `excluded_upstream_paths.csv` covers every omission.

## Raw-dataset publication policy

Four fixed-version PhysioNet trees (nsrdb, chfdb, mitdb, afdb version 1.0.0) are absent from the public working tree and reachable local publication history. They are reconstructed outside Git using `datasets/dataset_manifest.yaml`, 1,025 expected SHA256 entries, resume-capable fetch and read-only verification tools. Dataset DOI, ODC-By 1.0 and required citations are explicit. Locked `.mem`, split/evaluation data, XMODEL-to-RTL comparisons and board evidence remain retained.

## Technical evidence added

- Direct streaming-state inventory: `tables/streaming_state_inventory.csv`
- Claim `CLM-023`: no complete 1,800,000-sample raw-window storage in pure RTL
- Derived comparison: 21,600,000 bit = 2,700,000 byte ≈ 2.7 MB decimal, labelled `avoided full raw-input window storage`
- Digital signal flow: `figures/final/FIG-12_digital_processing_flow.svg`

## Claim and benchmark status

The report keeps public-dataset classification separate from product/clinical screening, board equivalence separate from label accuracy, and model-based analog evidence separate from physical silicon. The imported NO_BOARD benchmark records measured Exact C++ latency, cycle-derived FPGA-core latency, their scoped 32.912687x estimate, and estimated power/energy. Physical board timing, power and energy remain `PENDING_BOARD`.

The analog validation chain is now explicitly separated as MATLAB nominal pre-validation, XMODEL-aligned LTspice schematic implementation/regression, and SystemVerilog XMODEL behavioral/RTL handoff verification. The same ten-second, 10,000-sample ECG comparison records LTspice–XMODEL MAE 0.6445 LSB, RMS 1.3020 LSB, zero-lag correlation 0.999518, ±5 LSB coverage 98.74%, and ±10 LSB coverage 99.89%. These are schematic/behavioral model results, not transistor-level, post-layout, PCB, ADC-silicon, or live-electrode measurements.

## Size and integrity

Before/after measurements and blob verification are in `reports/REPOSITORY_SIZE_AUDIT.md` and `reports/HISTORY_REWRITE_RESULT.md`: working tree 2,307,174,104→140,346,925 bytes and `.git` 1,535,086,190→48,243,693 bytes. The final checker results are generated in `reports/integrated_repository_check.md` and the report-check output is recorded in the final response.

## Phased maintenance commits

1. Add reproducible dataset and licensing policy
2. Add streaming-state evidence and detailed architecture
3. Align integrated technical manuscript and claim registry
4. Finalize publication-readiness audit

History rewriting changes all affected commit IDs. No automatic push or force-push was performed.
