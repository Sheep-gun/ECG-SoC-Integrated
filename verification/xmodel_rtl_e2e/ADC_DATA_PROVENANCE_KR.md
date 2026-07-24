# ADC 데이터 출처 판정

## 결론

- 실제 XMODEL AFE–ADC 출력이며 직접 통합 RTL이 수락한 full-30분 dump: **4/36**.
- 위치: `datasets/xmodel_afe_adc_outputs/representative_4case/accepted_<case>.mem`.
- 생성 근거: `tb_snn_ecg_30min_mixed_e2e.sv`가 XMODEL `afe_adc`를 offset-binary→signed 12-bit로 변환하고, `sample_valid && sample_ready` 수락 때 3-hex/줄로 dump한다. `run_rep4_full30min.sh`가 이 dump를 생성한 뒤 같은 파일을 RTL replay manifest에 넣는다.
- 실제 존재 파일의 직접 통합 로그와 `rep4_e2e_verification.csv`가 독립적으로 같은 SHA-256을 기록한다.

## 기존 emulator 데이터

- `input_manifest_36case_sha256.csv`와 `part1_input_sha256_compare_36case.csv`의 36개 SHA는 `datasets/fullrec_afe*`/`sim_out/chunks36`에서 온 Python `afe_full.py` 계열 emulator chunk와 board-replay 입력의 동일성이다.
- 패키지의 `INTEGRATION_VERIFICATION_REPORT.md`와 `SPOTCHECK_XMODEL_vs_EMULATOR.md`가 이 점을 명시하며, 실제 XMODEL 60초 출력과 emulator는 전체 표본 기준 53.21%만 exact였다.
- 따라서 해당 36/36을 실제 XMODEL 출력 증명으로 사용하지 않았다.

## 결과 종류 구분

1. XMODEL–RTL 직접 통합 결과: `verification/xmodel_rtl_e2e/direct_verification/verification\integration_evidence/integ_<case>.log` — 대표 4개.
2. 기존 Vivado/XSim 기준값: `design/digital/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` — emulator 입력 기반 36개.
3. 실제 XMODEL 출력 replay 신 기준값: 이 실행의 `xsim_replay_results_present_cases.csv` — 현재 증거가 있는 4개만 생성.
4. 실제 XMODEL ADC 입력 manifest: `input_sha256_manifest_36case.csv` — 32개 누락을 숨기지 않고 기록.

## 누락 32개

- AFF_afdb_06995_chunk03
- AFF_afdb_06995_chunk05
- AFF_afdb_06995_chunk07
- AFF_afdb_06995_chunk10
- AFF_afdb_06995_chunk12
- AFF_afdb_06995_chunk14
- AFF_afdb_06995_chunk16
- AFF_afdb_06995_chunk18
- ARR_mitdb_105_chunk00
- ARR_mitdb_118_chunk00
- ARR_mitdb_202_chunk00
- ARR_mitdb_208_chunk00
- ARR_mitdb_214_chunk00
- ARR_mitdb_217_chunk00
- ARR_mitdb_220_chunk00
- ARR_mitdb_231_chunk00
- CHF_chfdb_chf06_chunk19
- CHF_chfdb_chf06_chunk32
- CHF_chfdb_chf07_chunk09
- CHF_chfdb_chf07_chunk29
- CHF_chfdb_chf09_chunk09
- CHF_chfdb_chf09_chunk29
- CHF_chfdb_chf15_chunk03
- CHF_chfdb_chf15_chunk09
- NSR_nsrdb_16272_chunk10
- NSR_nsrdb_16483_chunk10
- NSR_nsrdb_16483_chunk32
- NSR_nsrdb_16786_chunk11
- NSR_nsrdb_16786_chunk35
- NSR_nsrdb_19093_chunk10
- NSR_nsrdb_19093_chunk30
- NSR_nsrdb_19140_chunk20

재생성에는 원본 WFDB→PWL, XMODEL 2025.12/Questa 라이선스 환경, `optionB_gen_xmodel_chunks.sh` 또는 직접 통합 `run_e2e_all.sh`가 필요하다. 각 case에서 2초 settling 뒤 1,800,000 accepted signed code를 dump하고, dump SHA와 직접 통합 결과 로그를 함께 보존해야 한다.
