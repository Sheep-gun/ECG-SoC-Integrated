# 라이선스와 출처

이 저장소는 세 설계 구성과 검증 산출물을 하나로 모은 기술 저장소이며, 원저작물의
라이선스를 새로 부여하거나 변경하지 않는다. 각 구성의 고정 원본은 다음과 같다.

- MATLAB AFE–ADC: `ferocious-kiwi/ECG-SoC-MATLAB-AFE-ADC-Prevalidation` commit `907f7e1f081a9d6a5703a32095d962143315a192`
- AFE–ADC XMODEL: `Hwan-22/ECG-SoC` commit `4756a5086023547328ef44fd5fd87da3c250dc39`
- Digital RTL history: `Sheep-gun/SNN-ECG-Streaming-4-Class-Classifier` commit `c6b80de19cdcad5b7e43fe7835588b629d847f75`

상세 경로와 역할은 `project_registry/upstream_commits.yaml`, 현재 공개 파일의
SHA-256은 `project_registry/artifact_manifest.csv`에 기록한다. 원본 파일에 포함된
저작권과 라이선스 고지가 우선하며, 명시적인 라이선스가 없는 파일은 출처와 재현
근거를 보존하기 위해 포함한 것이지 추가 이용 권한을 부여하기 위한 것이 아니다.

PhysioNet의 NSRDB, CHFDB, MIT-BIH Arrhythmia Database와 AFDB 원시 waveform은
저장소에 포함하지 않는다. 버전, DOI, ODC-By 1.0 의무와 재구성 방법은
`datasets/DATASET_LICENSES.md`, `datasets/dataset_manifest.yaml` 및
`datasets/SHA256SUMS_EXPECTED.txt`에 기록한다. 프로젝트에서 만든 PWL, 고정 시험
입력과 검증 결과는 원 데이터의 라이선스와 출처를 변경하지 않는다.

개인 연락처, 학번, 서명과 직인이 포함된 신청서 원본 및 비공개 제출 자료는 Git에
포함하지 않는다. 공개 Figure는 `figures/final_submission/`의 파일만을 기준으로 한다.
