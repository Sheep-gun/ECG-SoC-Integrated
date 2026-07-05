# Strict Record-wise Dataset Audit

최종 30분 Final Membrane 검증은 `seed=20260808` strict record-wise split을 기준으로 한다. 이 split은 class별 30분 chunk 수를 train / validation / test = 17 / 8 / 9로 맞추면서, 같은 ECG source record에서 나온 chunk가 서로 다른 split에 들어가지 않도록 구성한다.

| 항목 | 값 |
|---|---|
| Dataset root | `fullrec_afe_30min_annotation_valid_balanced` |
| Split CSV | `reports/strict_recordwise_resplit_seed20260808/strict_recordwise_split.csv` |
| Split config | `configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json` |
| Manifest | `reports/strict_recordwise_resplit_seed20260808/recordwise_manifest.csv` |
| source_record_id overlap | 0 |
| physical_record_id overlap | 0 |
| class별 train / validation / test chunks | 17 / 8 / 9 |

| class | train records | validation records | test records | train chunks | validation chunks | test chunks |
|---|---:|---:|---:|---:|---:|---:|
| NSR | 9 | 4 | 5 | 17 | 8 | 9 |
| CHF | 6 | 4 | 4 | 17 | 8 | 9 |
| ARR | 17 | 8 | 9 | 17 | 8 | 9 |
| AFF | 2 | 1 | 1 | 17 | 8 | 9 |

Final Membrane parameter는 strict train / validation split에서만 선택하고, lock 이후 strict test split을 최종 1회 평가한다.
