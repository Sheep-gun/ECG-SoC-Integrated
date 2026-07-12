# Benchmark 한계

- 물리 보드 timing과 물리 전력은 측정하지 않았다.
- Exact C++는 hand-written single-thread transaction-level 구현이며 실제 RTL의 모든 clock toggle과 staging을 모사하는 simulator가 아니다.
- 32.912687배는 측정 CPU 지연시간과 cycle-derived FPGA-core 지연시간을 결합한 추정이며 측정 board speedup이 아니다.
- FPGA-core 범위에는 host transfer, MicroBlaze, UART, board software와 system overhead가 포함되지 않는다.
- 저장 데이터 처리시간과 live ECG 30분 관찰시간은 서로 다른 지표다.
- 0.099 W는 Vivado estimate이며 raw Vivado power report나 physical board measurement가 아니다.
- 0.005347247400 J/decision은 추정 전력과 cycle-derived 처리시간의 곱이다.
- Pure RTL과 전체 MicroBlaze system의 resource scope는 직접 비교할 수 없다.
- Python cycle model과 Verilator RTL simulation은 검증용 실행환경이며 대표 native CPU inference baseline이 아니다.
