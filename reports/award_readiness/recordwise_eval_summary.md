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

최종 보고서에는 strict train / validation에서 선택된 locked parameter와 strict test 최종 결과만 남긴다.
