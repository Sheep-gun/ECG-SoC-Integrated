# Strict Record-wise Final Dataset Summary

최종 30분 Final Membrane 검증은 `seed=20260808` strict record-wise dataset을 기준으로 진행한다.

| 항목 | 값 |
|---|---|
| Split CSV | `reports/strict_recordwise_resplit_seed20260808/strict_recordwise_split.csv` |
| Split config | `configs/recordwise_resplit_seed20260808/strict_recordwise_split_seed20260808.json` |
| source_record_id overlap | 0 |
| physical_record_id overlap | 0 |
| class별 train / validation / test chunks | 17 / 8 / 9 |

Final Membrane 후보는 SNN-inspired membrane 구조를 유지한다. 60초 snapshot에서 발생한 class spike와 evidence spike를 최종 class neuron membrane에 흥분성/억제성 current로 누적하고, 30분 window 끝에서 WTA로 NSR / CHF / ARR / AFF를 결정한다.

최종 locked result:

| 항목 | 결과 |
|---|---:|
| Selected candidate | `structural_guarded_silent_aff_1008710` |
| Train | 61/68 = 89.71% |
| Validation | 32/32 = 100.00% |
| Final test evaluation count | 1 |
| Final test chunk accuracy | 29/36 = 80.56% |
| Final test macro-F1 | 80.44% |
| Final test record-majority accuracy | 16/19 = 84.21% |
