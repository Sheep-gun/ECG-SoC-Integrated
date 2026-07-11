# AFE 36 chunk SHA256 bit-identity (vs digital board-replay input)

> AFE full-record output에서 slicing한 36개 30분 final-test chunk가 digital board-replay input과 SHA256 기준으로 **36/36 동일**.
> windowing: `start_sample = 2000 + chunk_id × 1,800,000`, 길이 1,800,000 (1 kSPS, 30 min). 생성기 `scripts/gen_sha256_bitidentity.py`.

| case_id | record | chunk | start_sample | gen_sha256(앞12) | board_sha256(앞12) | match |
|---|---|---|---|---|---|---|
| AFF_afdb_06995_chunk01 | AFF_afdb_06995 | 1 | 1,802,000 | `fe984d3ac495` | `fe984d3ac495` | true |
| AFF_afdb_06995_chunk03 | AFF_afdb_06995 | 3 | 5,402,000 | `a7d6dbd67666` | `a7d6dbd67666` | true |
| AFF_afdb_06995_chunk05 | AFF_afdb_06995 | 5 | 9,002,000 | `e7c0e16c7877` | `e7c0e16c7877` | true |
| AFF_afdb_06995_chunk07 | AFF_afdb_06995 | 7 | 12,602,000 | `a62fc2ba7a54` | `a62fc2ba7a54` | true |
| AFF_afdb_06995_chunk10 | AFF_afdb_06995 | 10 | 18,002,000 | `d30b6af5c747` | `d30b6af5c747` | true |
| AFF_afdb_06995_chunk12 | AFF_afdb_06995 | 12 | 21,602,000 | `6c1da7b13004` | `6c1da7b13004` | true |
| AFF_afdb_06995_chunk14 | AFF_afdb_06995 | 14 | 25,202,000 | `7220ebd13279` | `7220ebd13279` | true |
| AFF_afdb_06995_chunk16 | AFF_afdb_06995 | 16 | 28,802,000 | `48cab839586a` | `48cab839586a` | true |
| AFF_afdb_06995_chunk18 | AFF_afdb_06995 | 18 | 32,402,000 | `37ecff187d0b` | `37ecff187d0b` | true |
| ARR_mitdb_102_chunk00 | ARR_mitdb_102 | 0 | 2,000 | `99a94295c8ee` | `99a94295c8ee` | true |
| ARR_mitdb_105_chunk00 | ARR_mitdb_105 | 0 | 2,000 | `85f3a1fc2f06` | `85f3a1fc2f06` | true |
| ARR_mitdb_118_chunk00 | ARR_mitdb_118 | 0 | 2,000 | `cbe8acf71a01` | `cbe8acf71a01` | true |
| ARR_mitdb_202_chunk00 | ARR_mitdb_202 | 0 | 2,000 | `f5c9160169af` | `f5c9160169af` | true |
| ARR_mitdb_208_chunk00 | ARR_mitdb_208 | 0 | 2,000 | `1a8bf1ad0ac9` | `1a8bf1ad0ac9` | true |
| ARR_mitdb_214_chunk00 | ARR_mitdb_214 | 0 | 2,000 | `712de2a81e59` | `712de2a81e59` | true |
| ARR_mitdb_217_chunk00 | ARR_mitdb_217 | 0 | 2,000 | `00742ba0e768` | `00742ba0e768` | true |
| ARR_mitdb_220_chunk00 | ARR_mitdb_220 | 0 | 2,000 | `5c110d1f08e6` | `5c110d1f08e6` | true |
| ARR_mitdb_231_chunk00 | ARR_mitdb_231 | 0 | 2,000 | `d76ab5823cc7` | `d76ab5823cc7` | true |
| CHF_chfdb_chf06_chunk06 | CHF_chfdb_chf06 | 6 | 10,802,000 | `a309866d9e85` | `a309866d9e85` | true |
| CHF_chfdb_chf06_chunk19 | CHF_chfdb_chf06 | 19 | 34,202,000 | `391daf86765a` | `391daf86765a` | true |
| CHF_chfdb_chf06_chunk32 | CHF_chfdb_chf06 | 32 | 57,602,000 | `37a96f7d3458` | `37a96f7d3458` | true |
| CHF_chfdb_chf07_chunk09 | CHF_chfdb_chf07 | 9 | 16,202,000 | `66f80c091254` | `66f80c091254` | true |
| CHF_chfdb_chf07_chunk29 | CHF_chfdb_chf07 | 29 | 52,202,000 | `8b96d5a5f6f0` | `8b96d5a5f6f0` | true |
| CHF_chfdb_chf09_chunk09 | CHF_chfdb_chf09 | 9 | 16,202,000 | `f9c9c315d6b5` | `f9c9c315d6b5` | true |
| CHF_chfdb_chf09_chunk29 | CHF_chfdb_chf09 | 29 | 52,202,000 | `5b5d89f8424f` | `5b5d89f8424f` | true |
| CHF_chfdb_chf15_chunk03 | CHF_chfdb_chf15 | 3 | 5,402,000 | `0e2b422b4ba8` | `0e2b422b4ba8` | true |
| CHF_chfdb_chf15_chunk09 | CHF_chfdb_chf15 | 9 | 16,202,000 | `aab031ac3e00` | `aab031ac3e00` | true |
| NSR_nsrdb_16272_chunk03 | NSR_nsrdb_16272 | 3 | 5,402,000 | `fc6260465411` | `fc6260465411` | true |
| NSR_nsrdb_16272_chunk10 | NSR_nsrdb_16272 | 10 | 18,002,000 | `4b4bba5b02c6` | `4b4bba5b02c6` | true |
| NSR_nsrdb_16483_chunk10 | NSR_nsrdb_16483 | 10 | 18,002,000 | `5565bf678225` | `5565bf678225` | true |
| NSR_nsrdb_16483_chunk32 | NSR_nsrdb_16483 | 32 | 57,602,000 | `35fa40c7400b` | `35fa40c7400b` | true |
| NSR_nsrdb_16786_chunk11 | NSR_nsrdb_16786 | 11 | 19,802,000 | `094a1e3ff895` | `094a1e3ff895` | true |
| NSR_nsrdb_16786_chunk35 | NSR_nsrdb_16786 | 35 | 63,002,000 | `1062b5c0c705` | `1062b5c0c705` | true |
| NSR_nsrdb_19093_chunk10 | NSR_nsrdb_19093 | 10 | 18,002,000 | `ced832e3e528` | `ced832e3e528` | true |
| NSR_nsrdb_19093_chunk30 | NSR_nsrdb_19093 | 30 | 54,002,000 | `4f54ef41df1a` | `4f54ef41df1a` | true |
| NSR_nsrdb_19140_chunk20 | NSR_nsrdb_19140 | 20 | 36,002,000 | `6af06af53dd1` | `6af06af53dd1` | true |

**결과: SHA256 match 36/36.** 전 case에서 생성 chunk가 board-replay 입력과 바이트 단위 동일.
