# ECG-SoC 프로젝트 통합 구조 (2026-06-26 정리)

웨어러블 ECG 4-클래스 부정맥 감지 Mixed-Signal SoC (제27회 반도체설계대전, 한양대).
바탕화면에 흩어져 있던 모든 프로젝트 자료를 **이 `~/ECG-SoC/` 한 곳으로 통합**했습니다.
(바탕화면 원본은 **삭제하지 않고 그대로 보존** — 복사 방식.)

## 디렉터리 구조

```
~/ECG-SoC/
├── analog/          AFE XModel 행동모델 (ecg_afe_xmodel.sv) — 소스 정본
├── digital/         SNN core RTL 13개 .v (AFE 통합 시뮬용 서브셋, 구버전)
├── digital_block/   ★디지털 정본 스냅샷 (← 팀원 repo Sheep-gun/SNN-ECG-4-Class-Classifier)
│   ├── rtl/               현재 RTL 21개 (core 15 + axi 2 + common 1 + top/final/params)
│   ├── docs/              설계·검증 문서 5종(KR) + FINAL_REPORT_KR.md
│   ├── configs/ constraints/ reports/ ip_repo/ sim/ tools/
│   └── _UPSTREAM_COMMIT.txt   출처 커밋(91cad84, 2026-07-06)
├── fpga/            FPGA/Vivado 자료 (← 디지털 설계 블록 양건, 구버전 — digital_block/이 최신)
│   ├── SNN_ECG.srcs/      정식 Vivado RTL 소스
│   ├── constraints/       제약 파일 (XDC)
│   ├── bitstreams/        비트스트림 (.bit)
│   ├── reports/           합성/구현 리포트
│   ├── stitched_sources/  통합 소스
│   ├── vivado_project/    Vivado 프로젝트 (.runs/.cache 등 빌드캐시 제외)
│   └── README_OPEN_THIS_PROJECT.txt
├── tb/              테스트벤치 (tb_ecg_afe, tb_mixed_signal, tb_afe_batch 등)
├── scripts/         실행/분석 스크립트 (run_*, convert_mem, afe_emu, compare_val ...)
├── algorithm/       알고리즘 참고
├── data/            소규모 시뮬 데이터 (real_ecg_*.pwl, mem_*.mem)
├── docs/            ★모든 문서 통합
│   ├── AFE_verification_report.md      AFE 특성/검증
│   ├── integration_report.md          AFE↔디지털 통합 검증
│   ├── AFE_ADC_XADC_decision.md       ADC(XADC vs SAR) 결정 + 산출수치
│   ├── AFE_fullrecord_conversion_conditions.md  full-record 변환조건
│   ├── DIGITAL_BLOCK.md               ★디지털 블록 종합 개요(팀원 repo 분석)
│   ├── team_handoff/                  팀전달 문서 (.md/.pdf)
│   ├── digital_design/                SNN 설계문서 (docx: Actual/Pre-Project/Results + feature_docs)
│   ├── xmodel_info/                   XModel 참고자료 (← Xmodel 정보)
│   └── submission/                    대회 제출서류 (← 재출서류 모음)
├── datasets/        ★대용량 데이터셋 (git 제외 / .gitignore)
│   ├── strict_varlen/                 record-wise 4클래스 dataset (720, 60/90s)
│   ├── strict60_large/raw/            60s 1200(후보 1950) raw 입력 + manifest
│   ├── afe_output_xmodelmatch/        XModel 정합 AFE+ADC 출력 (1200 60s, signed+unsigned)
│   ├── fullrec_afe/                   ★full-record AFE+ADC (59 records 전체 stream) + .tar.gz
│   └── fullrec_afe_remaining/         ★나머지 68 records full-record + .tar.gz
├── sim_out/         시뮬 산출물/빌드 (git 제외)
├── Makefile         make sim / char / pli / vcd
├── README.md        프로젝트 개요
└── PROJECT_LAYOUT.md (이 문서)
```

## 핵심 정본(source of truth)
- **AFE 설계**: `analog/ecg_afe_xmodel.sv`
- **AFE+ADC 데이터(팀 학습용)**: `datasets/afe_output_xmodelmatch/` (XModel 검증, 평균 RMS 2.01 LSB)
- **디지털 블록(정본)**: `digital_block/` (팀원 repo 스냅샷; 최종모델 `structural_guarded_silent_aff_1008710`, final test 80.56%, HW 9719 LUT) · 개요 `docs/DIGITAL_BLOCK.md`. AFE 통합 시뮬용 서브셋=`digital/`
- **full-record AFE 데이터(디지털팀 전달)**: `datasets/fullrec_afe/`(59) + `fullrec_afe_remaining/`(68) = DB 전체, 1kSPS signed12 full stream
- **ADC 방향**: `docs/AFE_ADC_XADC_decision.md` (FPGA=XADC, 커스텀 SAR=SoC 설계물)

## 통합 시 의도적으로 제외한 항목 (바탕화면 원본에만 존재)
- **구버전 출력**: `afe_output_strict`(filter_mem) — `afe_output_xmodelmatch`로 대체됨
- **python-equiv 출력**: strict60_large unzipped의 {split}/{signed,unsigned} — XModel과 불일치(구버전)
- **중복 zip**: 모든 *.zip (폴더 원본과 중복)
- **빌드 아티팩트**: xsim_*, vivado .runs/.cache/.Xil, comp.log 등 (재생성 가능)
- **스냅샷 중복**: `프로젝트 파일 모음 6.22` (= 본 소스의 옛 복사본)
- **복구/정리 로그**: recovered_from_codex, restore_*, cleanup_* manifests

## 실행
- AFE 시뮬: `cd ~/ECG-SoC && make sim` (XModel+Questa, WSL, FPGA 보드 불필요)
- Mixed-signal 4클래스: `bash scripts/run_mixed_all.sh 60`
- AFE+ADC 에뮬레이터(전 데이터셋): `scripts/afe_emu.py` (생성기 참고)
