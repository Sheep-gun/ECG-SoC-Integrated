# License and provenance

This repository is an integration and evidence index, not a relicensing of the
three upstream projects. It is a **curated technical snapshot**, not a complete
byte-for-byte mirror of every upstream tracked path. Every retained imported
file under `components/` is a byte-for-byte export of a file tracked by the fixed upstream commit recorded in
`source_of_truth/upstream_commits.yaml` and
`source_of_truth/artifact_manifest.csv`.

Intentionally omitted upstream paths are enumerated in
`integration_evidence/excluded_upstream_paths.csv`. Fixed-version third-party
PhysioNet raw databases are additionally enumerated in
`integration_evidence/excluded_large_dataset_paths.csv` and reconstructed using
`datasets/dataset_manifest.yaml`, `datasets/SHA256SUMS_EXPECTED.txt`, and the
fetch/verification tools. The fixed upstream commits remain the authoritative
complete component snapshots.

The original copyright and license notices inside each component snapshot
remain controlling for that component. If an upstream file has no explicit
license, its presence here documents provenance only and grants no additional
rights. Newly authored integration documents and tools are project-internal
technical evidence unless the project owners publish a separate license.

Private contest forms, signatures, student identifiers, contact information,
and the final HWP/PDF report are intentionally excluded.

The four PhysioNet sources and their ODC-By 1.0 attribution/citation obligations
are documented in `datasets/DATASET_LICENSES.md`. Raw waveform files are not
bundled. Retained project-authored derived vectors and evaluation evidence do
not change the original dataset license or provenance.
