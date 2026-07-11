# Model S = Model A+ + EERG

EERG means Episodic Ectopic Rescue Gate.

## EERG Rule

```json
{
  "name": "EERG",
  "full_name": "Episodic Ectopic Rescue Gate",
  "rbbb_like_beat_count_eq": 0,
  "rbbb_segment_spike_count_eq": 0,
  "pre_qrs_bump_count_ge": 1,
  "early_count_ge": 10,
  "ecp_count_ge": 3,
  "pnn_mismatch_rate_le": 0.15,
  "rdm_avg_code_le": 5,
  "arr_boost": 25000
}
```

## Strict Test Summary

|model|segment_correct|segment_total|segment_accuracy|record_correct|record_total|record_accuracy|macro_f1|balanced_accuracy|ARR_recall|gate_applied|gate_success|gate_damage|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Model_A_plus|129|160|0.8063|17|19|0.8947|0.8059|0.8063|0.6500|0|0|0|
|Model_S_EERG|131|160|0.8187|18|19|0.9474|0.8193|0.8188|0.7000|6|2|0|

## Model S Test Segment Confusion

|actual|NSR|CHF|ARR|AFF|
|---|---|---|---|---|
|NSR|31|0|9|0|
|CHF|0|37|3|0|
|ARR|6|0|28|6|
|AFF|0|3|2|35|

## Model S Test Record Confusion

|actual|NSR|CHF|ARR|AFF|
|---|---|---|---|---|
|NSR|3|0|0|0|
|CHF|0|3|0|0|
|ARR|0|0|8|1|
|AFF|0|0|0|4|

## ARR Subtype Effect

|split|subtype|total|model_a_plus_correct|model_s_correct|delta|gate_applied|success|damage|
|---|---|---|---|---|---|---|---|---|
|test|RBBB-heavy|10|6|6|0|0|0|0|
|test|PVC-heavy|14|10|10|0|0|0|0|
|test|PAC-heavy|3|0|1|1|3|1|0|
|test|weak/boundary ARR|10|7|8|1|2|1|0|
|test|mixed|3|3|3|0|0|0|0|
