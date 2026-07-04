# Record-Wise Fixed-Model Evaluation

This is a retrospective source-record regrouping of the existing 136 chunks. It applies the already frozen Python golden rule set; it does not retrain or reselect thresholds.

| split | chunks | class-record pairs | correct | accuracy | macro-F1 | ARR recall | AFF recall |
|---|---|---|---|---|---|---|---|
| train | 67 | 35 | 62/67 | 92.54% | 92.50% | 82.35% | 94.12% |
| val | 34 | 17 | 33/34 | 97.06% | 97.21% | 100.00% | 100.00% |
| test | 35 | 18 | 30/35 | 85.71% | 86.88% | 88.89% | 77.78% |

## Split Composition

| split | NSR | CHF | ARR | AFF |
|---|---|---|---|---|
| train | 16 chunks / 9 recs | 17 chunks / 7 recs | 17 chunks / 17 recs | 17 chunks / 2 recs |
| val | 8 chunks / 4 recs | 10 chunks / 4 recs | 8 chunks / 8 recs | 8 chunks / 1 recs |
| test | 10 chunks / 5 recs | 7 chunks / 3 recs | 9 chunks / 9 recs | 9 chunks / 1 recs |

## Limitation

Because the final rule set was selected before this audit and the current repo contains chunk-level train/validation/test artifacts, this result is best treated as a record-wise leakage stress-test. A publishable strict record-wise claim would require freezing the protocol before model/rule search.
