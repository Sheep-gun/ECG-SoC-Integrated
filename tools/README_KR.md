# 재현 도구

- `check_clean_workspace.py`: 폴더 구조, 두 Vivado project, 개인 경로와 cache 잔존 여부 검사
- `check_integrated_technical_report.py`: 보고서 수치, 용어, 참고문헌과 evidence map 검사
- `check_integrated_repository.py`: 필수 설계·검증 artifact와 claim 경계 검사
- `build_artifact_manifest.py`: 현재 공개 파일의 크기와 SHA-256 manifest 생성
- `fetch_physionet_datasets.py`: 고정 PhysioNet 원본을 Git 밖의 작업 폴더에 내려받기
- `verify_physionet_datasets.py`: 원본 record와 SHA-256 검증
- `data/generate_locked_digital_36case.py`: 잠금 36-case 디지털 입력 재생성
- `verification/run_xmodel_adc_pure_rtl_replay.py`: 실제 XMODEL ADC dump의 Pure RTL replay 감사
- `vivado/`: Pure RTL hierarchy와 두 canonical Vivado project 검증 보조 도구

실행 순서와 필수 환경은 `REPRODUCIBILITY_KR.md`를 따른다.
