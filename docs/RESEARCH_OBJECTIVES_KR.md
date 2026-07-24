# 연구 목표

1 kSPS signed 12-bit ECG를 순차 처리해 60초 구간의 박동, 리듬과 파형 증거를 요약하고, 30개 Snapshot을 누적하여 NSR, CHF, ARR, AF를 판정하는 SNN 기반 accelerator IP를 구현한다.

현재 목표 검증 조건은 다음과 같다.

- locked final-test accuracy 80% 이상
- Pure RTL BRAM 0, DSP 0과 양의 timing slack
- Python, Exact C++, RTL/XSim과 FPGA의 기능 정합
- AFE–ADC XMODEL부터 RTL까지 signal handoff 추적

24시간 Holter 정확도, physical AFE/ADC, ASIC, post-layout와 silicon power는 후속 목표다.
