# FPGA Verification

## 대상 보드

- Board: Nexys A7-100T
- FPGA: Artix-7 `xc7a100tcsg324-1`
- Vivado: 2020.2

## Board Smoke Test

보드 데모 top은 버튼으로 4개 예시 class segment를 선택하고, Model S 결과를 7-segment에 표시합니다.

- BTNU: NSR 예시
- BTNL: ARR 예시
- BTND: CHF 예시
- BTNR: AFF 예시
- BTNC: 4개 예시 중 pseudo-random 선택

왼쪽 7-segment는 예측 class를 표시하고, 오른쪽 7-segment는 정답 여부에 따라 `CORR` 또는 `ERR`를 표시합니다.

## Implementation Summary

- Top module: `nexys_a7_model_s_smoke_top`
- Timing WNS: 4.242 ns
- Failing endpoints: 0
- DRC violations: 0
- Power estimate: 0.104 W

주의: board smoke top은 데모용 ROM, 7-segment controller, button logic을 포함합니다. 따라서 실제 classifier core resource와 board wrapper resource를 구분해서 해석해야 합니다.
