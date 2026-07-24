# 한계와 claim 경계

## 검증 완료

- strict source-record-wise locked 30분 final test
- 29/36 accuracy 80.56%, Macro-F1 80.44%
- MATLAB, LTspice와 XMODEL model-level AFE/ADC 정합
- Python, Exact C++, RTL/XSim 기능 정합
- Pure RTL and MicroBlaze post-route timing closure
- MicroBlaze FPGA replay class 36/36, membranes 144/144
- profiler counter 기반 FPGA core active time와 activity-based power estimate

## 조건부 또는 미완료

- 24시간 이상 Holter: 설계 지향점이며 실제 accuracy/time/power 미검증
- XMODEL raw full-30분 archive: 4/36만 현재 저장소에 보존
- 2.991 µW: 완전 power-gating을 가정한 산출값
- physical AFE PCB, ADC silicon, ASIC/post-layout, fabricated silicon: 미수행
- clinical validation와 medical-device certification: 미수행
- database–class confounding: 해소되지 않음

## 허용되는 표현

- “30분 public-dataset 조건에서 4-class 분류를 검증했다.”
- “24시간 이상 Holter ECG를 위한 streaming 확장을 지향한다.”
- “Pure RTL 구현에서 BRAM 0, DSP 0을 기록했다.”
- “FPGA 결과는 XSim 기준과 36/36 기능 정합했다.”
- “이상적 완전 power-gating 조건에서 2.991 µW로 산출된다.”

## 금지되는 표현

- “24시간 정확도와 실시간 동작을 검증했다.”
- “FPGA 또는 ASIC의 실측 전력이 2.991 µW다.”
- “36/36 기능 정합이므로 정확도 100%다.”
- “물리 AFE, ADC silicon 또는 fabricated SoC를 검증했다.”
- “임상 진단이 가능하거나 상용 wearable보다 우수하다.”
- “세계 최초” 또는 “동일 연구가 없다.”

## 제한된 최초성 표현

“검토한 대표 선행연구 범위에서는 NSR·CHF·ARR·AF 기록 분류, Snapshot별 질환 증거의 명시적 상태화, 장시간 증거 누적, RTL/IP/FPGA 구현과 MATLAB–XMODEL–RTL 추적성을 함께 적용한 사례를 확인하지 못하였다.”

이는 체계적 문헌고찰이나 세계 최초 주장으로 확대하지 않는다.
