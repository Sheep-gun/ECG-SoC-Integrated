# 설계 원본

이 폴더에는 수정과 재현의 출발점이 되는 아날로그 및 디지털 설계 원본만 둔다.

| 하위 경로 | 내용 |
|---|---|
| `analog/matlab/` | MATLAB AFE–ADC 공칭 설계와 사전 검증 |
| `analog/ltspice/` | LTspice AFE–S/H–ADC 회로와 비교 스크립트 |
| `analog/xmodel/` | SystemVerilog XMODEL과 실행 자료 |
| `digital/rtl/` | 고정 Pure RTL 분류 코어 |
| `digital/ip_repo/` | AXI 패키지형 SNN ECG accelerator IP |
| `digital/sim/` | RTL 및 AXI/IP testbench |
| `digital/constraints/` | FPGA constraint |
| `digital/scripts/`, `digital/tools/` | IP 생성, XSim, board replay 도구 |

Vivado project는 이 폴더가 아니라 `vivado/`에 있다.
