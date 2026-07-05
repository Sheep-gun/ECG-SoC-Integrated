# Strict Record-wise Structural Final Membrane Search

- Stage A: train/validation only
- ChatGPT 5.5 Pro session: `01KWRNZY09MSV2QHFQ54K07CYV`
- Final-test used for structure selection: `false`
- Final-test used for parameter search: `false`
- Random seed: `5610808`
- Candidates evaluated: `3000000`
- Passing candidates train>=61/68 and validation>=30/32: `6569`
- Selected candidate: `structural_guarded_silent_aff_1008710`

| split | correct/total | accuracy | macro-F1 | balanced accuracy |
|---|---|---|---|---|
| train | 61/68 | 89.71% | 89.91% | 89.71% |
| validation | 32/32 | 100.00% | 100.00% | 100.00% |

## Top Candidates

| rank | candidate | train | validation | val_macro_f1 | train_macro_f1 |
|---|---|---|---|---|---|
| 1 | structural_guarded_silent_aff_1008710 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 2 | structural_guarded_silent_aff_1657148 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 3 | structural_guarded_silent_aff_1866767 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 4 | structural_guarded_silent_aff_2171897 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 5 | structural_guarded_silent_aff_1942262 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 6 | structural_guarded_silent_aff_2924958 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 7 | structural_guarded_silent_aff_0019324 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 8 | structural_guarded_silent_aff_1020898 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 9 | structural_guarded_silent_aff_1890395 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 10 | structural_guarded_silent_aff_0800469 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 11 | structural_guarded_silent_aff_0184961 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 12 | structural_guarded_silent_aff_1942416 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 13 | structural_guarded_silent_aff_1255310 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 14 | structural_guarded_silent_aff_2016236 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 15 | structural_guarded_silent_aff_0363758 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 16 | structural_guarded_silent_aff_1135074 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 17 | structural_guarded_silent_aff_2647431 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 18 | structural_guarded_silent_aff_2749910 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 19 | structural_guarded_silent_aff_1139895 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |
| 20 | structural_guarded_silent_aff_0574087 | 61/68 | 32/32 | 1.0 | 0.8990641711229946 |

## Selected Params

```json
{
  "aff_cnt": 12,
  "aff_chf_cnt": 14,
  "aff_morph_le": 3000,
  "aff_rhythm_ge": 12000,
  "aff_qrs_le": 1000,
  "nsr_cnt": 4,
  "nsr_chf_cnt": 8,
  "nsr_morph_le": 100,
  "nsr_abn_le": 60,
  "nsr_qrs_le": 10,
  "nsr_ect_le": 40,
  "arr_nsr_nsr_cnt": 16,
  "arr_nsr_morph_ge": 3500,
  "arr_nsr_pre_ge": 2600,
  "arr_nsr_arr_cnt": 4,
  "arr_nsr_qrs_high_le": 100,
  "arr_nsr_rbbb_high_le": 16,
  "arr_nsr_arr_low_le": 2,
  "arr_nsr_qrs_low_le": 30,
  "arr_nsr_ect_low_le": 40,
  "arr_nsr_rhythm_low_le": 10000,
  "arr_aff_aff_cnt": 10,
  "arr_aff_arr_cnt": 3,
  "arr_aff_morph_ge": 500,
  "arr_aff_ect_ge": 400,
  "arr_aff_qrs_le": 200,
  "aff_boost": 80,
  "aff_inh_chf": 40,
  "aff_inh_arr": 0,
  "nsr_boost": 40,
  "nsr_inh_chf": 40,
  "nsr_inh_arr": 20,
  "arr_nsr_boost": 40,
  "arr_nsr_inh_nsr": 40,
  "arr_nsr_inh_chf": 40,
  "arr_nsr_inh_aff": 10,
  "arr_aff_boost": 40,
  "arr_aff_inh_aff": 40,
  "candidate_id": "structural_guarded_silent_aff_1008710",
  "family": "F1_F6_F10_guarded_rescue_silent_aff"
}
```
