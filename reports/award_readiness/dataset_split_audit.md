# Dataset Split Audit

This audit uses the current 30-minute dataset and the fixed Python chunk loader.

- Dataset root: `C:\Users\YangGeon\SNN ECG Classifier\fullrec_afe_30min_annotation_valid_balanced`
- Manifest: `C:\Users\YangGeon\SNN ECG Classifier\fullrec_afe_30min_annotation_valid_balanced\annotation_valid_balanced_30min_manifest.csv`
- Chunks inspected: 136
- Class-record pairs inspected: 70
- Class-record pairs spanning multiple current splits: 33

| class | chunks | unique_records | train_records | val_records | test_records | overlap_count |
|---|---|---|---|---|---|---|
| NSR | 34 | 18 | 17 | 7 | 9 | 15 |
| CHF | 34 | 14 | 14 | 6 | 9 | 14 |
| ARR | 34 | 34 | 17 | 8 | 9 | 0 |
| AFF | 34 | 4 | 4 | 4 | 4 | 4 |

## Interpretation

The current train/validation/test organization is chunk-level balanced. Some source records appear in more than one current split, so the existing 88.89% test result must not be described as strict record-wise generalization.

Detailed record overlap tables:

- `reports/award_readiness/dataset_split_leakage_detail.csv`
- `reports/award_readiness/dataset_manifest_split_trace.csv`
