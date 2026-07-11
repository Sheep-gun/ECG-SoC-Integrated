# Reproducible PhysioNet dataset package

이 공개 저장소는 PhysioNet의 raw waveform을 복제해 포함하지 않는다. 고정 버전, 사용 record, 공식 URL, DOI, license, citation, 예상 SHA256은 `dataset_manifest.yaml`, `DATASET_LICENSES.md`, `SHA256SUMS_EXPECTED.txt`에 고정한다. 프로젝트가 생성한 locked `.mem`, split manifest, 평가 CSV, board-replay 및 integration evidence는 그대로 유지한다.

기본 다운로드 위치는 저장소 밖의 `../_ecg_soc_physionet`이다.

```powershell
python tools/fetch_physionet_datasets.py
python tools/verify_physionet_datasets.py --data-root ..\_ecg_soc_physionet
```

특정 데이터베이스만 받을 때는 `--database nsrdb`처럼 지정한다. fetch는 `.part` 파일과 HTTP Range를 사용해 중단된 다운로드를 이어받고, 이미 SHA256이 일치하는 파일은 다시 받지 않는다. verify는 파일을 변경하지 않으며 JSON summary를 출력한다.

다운로드와 사용은 각 데이터베이스의 Open Data Commons Attribution License v1.0 및 PhysioNet attribution 조건을 따라야 한다. 데이터베이스와 class가 결합된 현재 평가의 domain-confounding 한계는 `docs/DATASET_DOMAIN_CONFOUNDING_KR.md`에 공개한다.
