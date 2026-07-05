# Strict Record-wise Dataset Summary

최종 제출 문서에서는 `seed=20260808` strict record-wise split을 기준으로 한다. 이 split은 30분 chunk가 아니라 `source_record_id` 단위로 train / validation / test를 나누며, label-stripped `physical_record_id` 기준으로도 split 간 overlap 0을 확인한다.

| class | train records | validation records | test records | train chunks | validation chunks | test chunks |
|---|---:|---:|---:|---:|---:|---:|
| NSR | 9 | 4 | 5 | 17 | 8 | 9 |
| CHF | 6 | 4 | 4 | 17 | 8 | 9 |
| ARR | 17 | 8 | 9 | 17 | 8 | 9 |
| AFF | 2 | 1 | 1 | 17 | 8 | 9 |

Final Membrane parameter는 strict train / validation split에서만 선택하고, parameter lock 이후 strict test split을 최종 1회 평가하는 기준으로 보고한다.
