# 검증과 구현 증거

| 하위 경로 | 내용 |
|---|---|
| `xmodel_rtl_e2e/` | 실제 보유 XMODEL ADC 입력의 Pure RTL replay와 출처 |
| `fpga_implementation/` | Vivado 배치·배선, 자원, timing 원본 |
| `integration_evidence/` | 통합 전후 상태와 의도적 제외 자료 |
| `timing_optimization/` | critical path 관측과 pipeline 최적화 이력 |

실제 full-30분 XMODEL ADC dump는 4개만 보존되어 있으며, 나머지 32개가 존재하는 것처럼 해석하지 않는다.
