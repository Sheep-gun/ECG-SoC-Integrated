# Integration audit

## Result

The independent integrated technical repository is complete at this path and branch:

- Repository: `ECG-SoC-Integrated`
- Branch: `main`
- Own Git metadata: `.git/` present
- Remote: none configured; nothing was pushed
- Integrity checker: PASS, 163 rules, 0 conflicts
- Final commit: resolve with `git rev-parse HEAD` after this audit commit

## Fixed component provenance

| Component | Normalized origin | Fixed imported commit | Commit title | Owner | Imported files |
|---|---|---|---|---|---:|
| MATLAB nominal pre-validation | `https://github.com/ferocious-kiwi/ECG-SoC-MATLAB-AFE-ADC-Prevalidation` | `907f7e1f081a9d6a5703a32095d962143315a192` | Move package contents to repository root | 서민우 | 136 |
| AFE+ADC XMODEL | `https://github.com/Hwan-22/ECG-SoC` | `4756a5086023547328ef44fd5fd87da3c250dc39` | 2차 리뷰 반영: claim 강도 조정 + threshold artifact + path portability | 이수환 | 1,497 |
| Digital accelerator | `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier` | `c6b80de19cdcad5b7e43fe7835588b629d847f75` | Clarify digital ownership across final documentation | 양건 | 257 |

Total imported files in `artifact_manifest.csv`: 1,890. Every imported file records upstream path, integrated path, size and SHA256.

## Upstream state before and after

| Component | Branch | Active HEAD | Before tracked status | After tracked status | Untracked status |
|---|---|---|---|---|---|
| MATLAB | `main` | `907f7e1f...` | clean | clean | none before/after |
| XMODEL | `main` | `4756a508...` | clean | clean | none before/after |
| Digital | `codex/accelerator-benefit-benchmark` | `5b6f0119...` | concurrent benchmark modifications only | concurrent benchmark modifications only | benchmark `tools/cpp/`, `obj/`, and `tmp/` paths continued to evolve |

All three branches and active HEADs remained unchanged. The digital tracked-status path list changed while the independently authorized benchmark task continued, but every changed tracked path remained under `benchmarks/accelerator_benefit/`. Integration exported fixed Git object `c6b80de...`; it did not read or write these worktree bytes. `tmp/` and `tmp/oss-cad/` were not deleted, moved, renamed, cleaned, reset, stashed, added, committed, or imported.

Authoritative full status snapshots:

- `integration_evidence/upstream_status_before.json`
- `integration_evidence/upstream_status_after.json`

No checkout, switch, reset, clean, stash, pull, merge, add or commit was executed in an upstream repository.

## Nested repository safety

The parent digital repository initially saw the nested directory as untracked. A local-only `/ECG-SoC-Integrated/` entry was added to the parent `.git/info/exclude`; the parent tracked `.gitignore` was not edited. The integrity checker confirms that no integrated path is present in the parent index.

## Import method and exclusions

`tools/import_upstream_repositories.py` discovers sources by normalized origin, verifies fixed commits, exports with `git archive`, rejects archive traversal/links, and regenerates file hashes. The default policy rejects tracked modifications. This run used the explicitly audited digital benchmark exception authorized by the user; the exported commit remained `c6b80de...`.

Four tracked upstream files were intentionally omitted:

1. `components/afe_xmodel` upstream `docs/digital_design/Results/~$del_S_FPGA_Verification_Report.docx` — temporary Office lock file
2. `components/afe_xmodel` upstream `docs/submission/[공고문] 제27회 대한민국반도체설계대전.pdf` — contest notice/submission material
3. `components/afe_xmodel` upstream `docs/submission/[참가신청서] 제27회 대한민국 반도체설계대전.hwp` — application form
4. `components/afe_xmodel` upstream `docs/submission/[참가신청서] 제27회 대한민국 반도체설계대전.pdf` — application form

Their upstream SHA256 and sizes remain in `integration_evidence/excluded_upstream_paths.csv`. No upstream `.git`, untracked benchmark tooling, cache, virtual environment, final private report or personal application information was imported.

## Repository size and large files

- Working-tree files excluding `.git`: 2,307,102,761 bytes (2.149 GiB)
- Repository including current `.git`: 3,842,065,001 bytes (3.578 GiB at audit time)
- Files at least 50 MiB: 15
- Files at least 100 MiB: 0

The 15 large files are public chfdb `.dat` records under `components/afe_xmodel/algorithm/person_data/chfdb/1.0.0/`, each about 50.9–51.5 MiB. They were already tracked technical dataset evidence in the fixed XMODEL commit. A future remote publication should consider Git LFS or a reproducible dataset-fetch manifest; this local independent repository intentionally preserves the commit-pinned evidence snapshot.

## Source of truth created

- `upstream_commits.yaml`
- `global_metrics.yaml` with 33 verified metrics and null benchmark fields
- `claim_registry.csv` with SAFE/CAREFUL/FORBIDDEN/PENDING_EXTERNAL_WORK controls
- `artifact_manifest.csv` with 1,890 SHA256 rows
- `ownership_matrix.csv`
- `terminology.yaml`
- `external_reference_registry.csv`

## Research and technical documents created

Research positioning:

- `RESEARCH_BACKGROUND_KR.md`
- `PROBLEM_DEFINITION_KR.md`
- `RESEARCH_OBJECTIVES_KR.md`
- `CONTRIBUTIONS_AND_NOVELTY_KR.md`
- `LIMITATIONS_AND_CLAIM_BOUNDARY_KR.md`

Technical integration:

- `SYSTEM_OVERVIEW_KR.md`
- `OWNERSHIP_AND_HANDOFF_KR.md`
- `DATASET_AND_EVALUATION_KR.md`
- `DATASET_DOMAIN_CONFOUNDING_KR.md`
- `MIXED_SIGNAL_VERIFICATION_KR.md`
- `DIGITAL_ARCHITECTURE_KR.md`
- `HARDWARE_IMPLEMENTATION_KR.md`
- `INTEGRATION_VERIFICATION_KR.md`
- `REPORT_EVIDENCE_MAP_KR.md`
- `INTEGRATION_METHOD.md`

## Figures and tables

Eleven non-benchmark SVG figures were generated and XML-validated:

1. long-window motivation
2. complete system flow
3. ownership/handoff
4. Snapshot/Final Membrane architecture
5. strict record-wise protocol
6. MATLAB nominal summary
7. XMODEL scope
8. signed-stream handoff
9. digital validation hierarchy
10. classification summary
11. confounding/claim boundary

`figures/FIGURE_INDEX.md` records owner, source files, source commits, source-data path, caption, scope and limitation for each figure. Three verified tables cover classification, hardware implementation and integration evidence. No latency, throughput, speedup, power, energy or board-timing figure/table was created.

## Integrity and claim audit

`tools/check_integrated_repository.py` passed 163 checks covering:

- origin and fixed-commit identity
- imported-file hashes and exact component file sets
- no nested upstream `.git` or benchmark-tool import
- privacy/application exclusions
- required structure and evidence paths
- metric/ownership/cadence consistency
- validation-versus-generalization wording
- board equivalence versus label accuracy
- clinical/physical claim boundaries
- database-class confounding disclosure
- external-reference registration
- benchmark nulls and placeholder
- parent repository index isolation

Report: `reports/integrated_repository_check.md`.

## Unresolved evidence and bounded scope

- Accelerator-benefit benchmark: `PENDING_EXTERNAL_BENCHMARK_IMPORT`; all latency/throughput/speedup/power/energy fields are null, not zero.
- Database-class confounding remains; stronger generalization requires same-acquisition multi-class or explicit cross-domain validation.
- Physical AFE PCB, ADC silicon, transistor/post-layout, fabricated SoC, live electrode and clinical validation were not performed.
- No fabricated references or commercial-product performance numbers are used. Registered external sources cover only conservative background and dataset provenance.

## Next step: benchmark import

When the independent benchmark work is complete, pin its repository/branch commit, verify its input hashes against the locked component input, record environment and measurement scope, distinguish measured/cycle-derived/estimated values, import raw/result CSVs, update `global_metrics.yaml` and `claim_registry.csv`, then regenerate figures and rerun the integrity checker. Do not overwrite the locked model or final-test results.

## Next step: private HWP report

Use `docs/REPORT_EVIDENCE_MAP_KR.md` as the chapter-by-chapter evidence map and `claim_registry.csv` as the wording gate. Keep the contest HWP/PDF, application forms, signatures, student IDs, addresses, phone numbers and private email data outside Git. The private report should foreground the long-window multi-timescale classification architecture, then use accelerator benchmark results only as supporting evidence after their independent import is verified.

## Post-integration technical manuscript

The complete Korean technical source manuscript was added after the base integration audit:

- `reports/INTEGRATED_TECHNICAL_REPORT_KR.md`
- `reports/INTEGRATED_TECHNICAL_REPORT_REVIEW_CHECKLIST.md`
- `reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv`
- `tools/check_integrated_technical_report.py`

The manuscript synthesizes the fixed MATLAB, XMODEL and digital evidence into one continuous report-ready narrative while preserving the official private HWP/application as a future out-of-Git deliverable. The report-specific checker passed 199 rules with zero conflicts, and the unchanged repository checker passed 163 rules with zero conflicts before the manuscript commit.

## Phased integration commits

1. `f0fd18c` — initialize independent integration repository
2. `210a4ac` — import commit-pinned component snapshots
3. `add9b4d` — establish integrated source of truth
4. `9333a9c` — define research positioning and claim boundaries
5. `0728482` — document end-to-end technical integration
6. `671cb11` — complete final-facing integrated repository
7. final audit commit — this document and final verification evidence
