# 36-case Strict Final Test Full-record Board Replay

이 문서는 strict record-wise final_test 36개 30분 chunk에 대한 Vitis/MicroBlaze board replay batch 상태를 정리한다.
실제 board transcript가 없는 case는 완료로 세지 않는다.

| Metric | Result |
|---|---:|
| Cases requested | 36 |
| Cases completed | 36 |
| Samples per case | 1,800,000 |
| Snapshots per case | 30 |
| Board-vs-expected final_pred PASS | 36/36 |
| Board-vs-expected final_mem exact PASS | 36/36 |
| Board classification accuracy vs label | 29/36 |
| Pending cases | 0 |
| Final_mem exact mismatch cases | 0 |
| Other failed/invalid cases | 0 |

| case_id | label | expected_pred | board_pred | pred_match | mem_match | samples | snapshots | status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `AFF_afdb_06995_chunk01` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk03` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk05` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk07` | AFF | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk10` | AFF | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk12` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk14` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk16` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `AFF_afdb_06995_chunk18` | AFF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_102_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_105_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_118_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_202_chunk00` | ARR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_208_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_214_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_217_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_220_chunk00` | ARR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `ARR_mitdb_231_chunk00` | ARR | 2 | 2 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf06_chunk06` | CHF | 1 | 1 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf06_chunk19` | CHF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf06_chunk32` | CHF | 1 | 1 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf07_chunk09` | CHF | 1 | 1 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf07_chunk29` | CHF | 3 | 3 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf09_chunk09` | CHF | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf09_chunk29` | CHF | 1 | 1 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf15_chunk03` | CHF | 1 | 1 | 1 | 1 | 1800000 | 30 | PASS |
| `CHF_chfdb_chf15_chunk09` | CHF | 1 | 1 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_16272_chunk03` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_16272_chunk10` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_16483_chunk10` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_16483_chunk32` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_16786_chunk11` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_16786_chunk35` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_19093_chunk10` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_19093_chunk30` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |
| `NSR_nsrdb_19140_chunk20` | NSR | 0 | 0 | 1 | 1 | 1800000 | 30 | PASS |

이 결과는 physical AFE/ADC 검증이 아니라, locked RTL/IP bitstream이 Vitis/MicroBlaze board path에서 full-record input stream을 끝까지 처리하는지 확인하는 board-level integration evidence이다.

## Artifacts

- Case manifest: `reports/final/board_replay_36_cases.csv`
- Expected-vs-board CSV: `reports/final/board_replay_36_expected_vs_board.csv`
- Batch summary JSON: `reports/final/board_replay_36_batch_summary.json`
- Transcripts: `reports/final/board_replay_36/transcripts`
- Parsed JSON: `reports/final/board_replay_36/parsed`
