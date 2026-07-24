# Reproducible PhysioNet dataset package

이 공개 저장소는 PhysioNet의 raw waveform을 복제해 포함하지 않는다. 고정 버전, 사용 record, 공식 URL, DOI, license, citation, 예상 SHA256은 `dataset_manifest.yaml`, `DATASET_LICENSES.md`, `SHA256SUMS_EXPECTED.txt`에 고정한다. 프로젝트가 생성한 locked `.mem`, split manifest, 평가 CSV, board-replay 및 integration evidence는 그대로 유지한다.

기본 다운로드 위치는 저장소 밖의 `../_ecg_soc_physionet`이다.

PhysioNet의 공식 `SHA256SUMS.txt`에는 현재 고정 버전 HTTP 디렉터리에서
제공되지 않는 역사적 편집기 백업 항목(`*.hea-`, `*.atr-` 등)이 포함되어
있다. fetch와 verify는 이를 명시적으로 제외하고 실제 배포 파일만 검증한다.

```powershell
python tools/fetch_physionet_datasets.py
python tools/verify_physionet_datasets.py --data-root ..\_ecg_soc_physionet
```

고정 디지털 36-case 입력은 raw waveform과 보존된 AFE 변환 규칙에서 다시
생성한다. 이 데이터는 실제 XMODEL dump가 아니라, 과거 FPGA/XSim 검증에
사용한 signed 12-bit 입력을 재현한 파생 데이터이다. 각 파일은 1,800,000
표본이며 고정 board-replay manifest의 SHA-256과 일치해야 한다.

```powershell
python tools/data/generate_locked_digital_36case.py
python models/digital_equivalence/tools/check_python_equivalence.py --workers 4
```

재생성에 사용한 Python 패키지 버전은 `datasets/requirements-reproduction.txt`에
고정한다.

기본 출력 위치는 저장소 밖의 `../generated_rtl_fpga_test_inputs_36case`이다. 생성 manifest와 실행
환경은 각각 `locked_digital_36case_manifest.csv`와
`locked_digital_36case_environment.json`에 기록된다. 실제 full-30분 XMODEL
AFE-ADC 출력은 `datasets/xmodel_afe_adc_outputs/`에 보존된 4개만 직접 근거로
취급하며, 두 데이터 범주를 서로 대체하거나 혼용하지 않는다.

특정 데이터베이스만 받을 때는 `--database nsrdb`처럼 지정한다. fetch는 `.part` 파일과 HTTP Range를 사용해 중단된 다운로드를 이어받고, 이미 SHA256이 일치하는 파일은 다시 받지 않는다. verify는 파일을 변경하지 않으며 JSON summary를 출력한다.

다운로드와 사용은 각 데이터베이스의 Open Data Commons Attribution License v1.0 및 PhysioNet attribution 조건을 따라야 한다. 데이터베이스와 class가 결합된 현재 평가의 domain-confounding 한계는 `docs/DATASET_DOMAIN_CONFOUNDING_KR.md`에 공개한다.
