# 재현 안내

## 고정 환경

- Digital fixed source: `c6b80de19cdcad5b7e43fe7835588b629d847f75`
- Timing pipeline history: `c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa`, `5e2e5d0a46be47d8086b8642e055066079bfa4e6`
- MATLAB fixed source: `907f7e1f081a9d6a5703a32095d962143315a192`
- XMODEL fixed source: `4756a5086023547328ef44fd5fd87da3c250dc39`
- Vivado: 2020.2
- FPGA: Artix-7 XC7A100T-CSG324-1
- Stream: 1 kSPS signed 12-bit two's complement

## 1. 데이터 준비

```powershell
python tools/fetch_physionet_datasets.py
python tools/verify_physionet_datasets.py
python tools/data/generate_locked_digital_36case.py
```

PhysioNet raw data와 generated input은 Git 외부 workspace path에 생성한다. checksum과 record 목록은 `datasets/dataset_manifest.yaml`을 따른다.

## 2. Python과 Exact C++

Python equivalence:

```powershell
python models/digital_equivalence/tools/check_python_equivalence.py
```

Exact C++:

```powershell
cmake -S models/digital_equivalence/exact_cpp -B build/exact_cpp
cmake --build build/exact_cpp --config Release
python models/digital_equivalence/exact_cpp/tools/run_cpp_equivalence.py
```

Exact C++ 결과를 benchmark로 사용하기 전 fixed-width, module trace, sample state, Snapshot과 final equivalence gate를 모두 통과해야 한다.

## 3. Pure RTL Vivado

```powershell
vivado -mode batch -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl
```

GUI project:
`vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr`

## 4. MicroBlaze Vivado

GUI project:
`vivado/microblaze/SNN_ECG_MB_FULL_REPLAY.xpr`

Project IP repository path가 이동한 경우 `design/digital/ip_repo/`를 지정하고 IP Catalog refresh 후 Block Design을 validate한다.

## 5. raw XMODEL output replay

```powershell
python tools/verification/run_xmodel_adc_pure_rtl_replay.py
```

현재 저장소는 raw full-30분 XMODEL accepted file 4개만 보존한다. 32개를 재생성하지 않으면 이 단계는 4-case audit로 완료되며 36-case raw replay PASS를 선언하지 않는다.

## 6. repository 검사

```powershell
python tools/check_clean_workspace.py
python tools/check_integrated_technical_report.py
python tools/check_integrated_repository.py
git diff --check
```

검사기는 핵심 파일, 수치, 두 Vivado project, claim/evidence mapping, private path와 절대경로 누출을 fail-closed로 검사한다.
