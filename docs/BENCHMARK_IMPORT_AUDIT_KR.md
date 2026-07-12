# 가속기 Benchmark 반입 감사

## 원천

- 저장소: `https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier`
- 원격 branch: `main`
- 반입 commit: `09e4d840827ad20856f5e23be4743ddd01565e30`
- commit title: `Merge Exact C++ native CPU baseline`
- 고정 분류기/RTL authority: `c6b80de19cdcad5b7e43fe7835588b629d847f75`

Benchmark commit은 고정 분류기, 문턱값, RTL, 최종 시험 예측을 변경한 새 모델이 아니다. 고정 설계와 동일한 36개 입력에서 Exact C++ 등가성을 확립한 뒤 CPU 시간을 측정하고, canonical RTL cycle count와 100 MHz 구현 clock으로 accelerator-core 처리시간을 산출한 후속 근거다.

## 반입 판단

대표 CPU 기준선은 Python cycle model이나 Verilator host simulation이 아니라 hand-written single-thread transaction-level Exact C++로 고정한다. Python은 검증 모델로 느리고, Verilator는 RTL simulation runtime이므로 대표 CPU inference speedup에 사용하지 않는다.

보고 가능한 대표 비교는 다음과 같다.

`1777.699800 ms / 54.012600 ms = 32.912687×`

분자는 36 cases × 10 measured runs의 Exact C++ kernel 전체 중앙값이다. 분모는 5,401,260 cycles와 100 MHz에서 얻은 cycle-derived FPGA accelerator-core 지연시간이다. 따라서 이 비율은 측정 board speedup이 아니라 **Exact C++ 대 cycle-derived FPGA-core speedup estimate**다.

## 등가성 gate

- final prediction: 36/36
- final membrane: 144/144
- Snapshot boundary: 1,080/1,080
- accepted-sample state hash: 240,000/240,000
- fixed-width checks: 793,595, failure 0
- module/adversarial microtrace: 18/18
- Debug/Release output identity: 36/36

## 남은 경계

- 54.012600 ms는 저장 데이터의 accelerator-core active processing time이다.
- live ECG 최종 판정은 현재 입력 창 30분의 관찰을 필요로 한다.
- host transfer, MicroBlaze, UART와 board software overhead는 포함하지 않는다.
- 0.099 W와 0.005347247400 J/decision은 Vivado estimate 기반 추정이다.
- physical board timing, power와 energy는 `PENDING_BOARD`다.
- 분류 정확도 29/36 및 record-majority 16/19는 바뀌지 않는다.

## 선별 반입 파일

대회 보고서가 직접 인용하는 요약 report, Exact C++ 비교 CSV, RTL cycle JSON, power/energy CSV와 post-benchmark equivalence만 통합 저장소에 보존하였다. 전체 benchmark source, 원시 720-run CSV, executable과 board 준비 package는 원본 저장소의 지정 commit에서 추적한다.
