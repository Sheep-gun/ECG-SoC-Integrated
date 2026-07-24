# Vivado 프로젝트

유지하는 `.xpr`은 아래 두 개뿐이다.

| 목적 | 실행할 project |
|---|---|
| Pure RTL hierarchy와 elaborated schematic 확인 | `pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr` |
| AXI IP, MicroBlaze, implementation 및 FPGA replay | `microblaze/SNN_ECG_MB_FULL_REPLAY.xpr` |

`pure_rtl/evidence/`에는 Pure RTL hierarchy 선택 목록과 schematic 출력 안내가 있으며, `project_verification.txt`에는 두 project의 source/top 검증 결과가 기록된다.
