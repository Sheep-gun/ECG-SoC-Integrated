# 한계와 claim 경계

## 허용되는 핵심 주장

- Holter-oriented long-window, multi-timescale, SNN-inspired ECG classification architecture
- 1 kSPS signed 12-bit stream과 60초 Snapshot/30분 Final Membrane 구조
- locked final-test chunk 29/36=80.56%, record-majority 16/19=84.21%
- pure RTL resource/timing closure와 packaged IP/FPGA replay
- board final_pred/final_mem 36/36 functional equivalence
- AFE input SHA256 36/36와 canonical cadence AFE-to-RTL 36/36 reproduction
- MATLAB/LTspice/XMODEL 기반 공칭·schematic·behavioral AFE/ADC verification

## 주의해서 표현할 주장

`Holter-oriented`는 장시간 ECG 구조의 설계 동기를 뜻하며 임상 Holter 인증이 아니다. `SNN-inspired`는 event/state와 membrane-like accumulation을 뜻하며 trained deep SNN이나 생물학적 등가가 아니다. `low-resource`는 0 BRAM/0 DSP와 구현 자원으로 범위를 한정한다. NO_BOARD benchmark의 처리시간 비율과 추정 전력은 보고할 수 있지만 physical board의 speedup·power·energy superiority는 주장하지 않는다.

Analog robustness는 LTspice schematic stress와 XMODEL representative regression이 지원하는 model-based 범위로만 쓴다. LTspice–XMODEL 10초 비교의 ±5/±10 LSB coverage를 sample-wise bit-exact로 표현하지 않는다. R/C mismatch의 30분 final_pred stability는 직접 전체 sweep이 아니라 equivalence-based argument임을 유지한다. 60 Hz target 결과를 50 Hz 환경 성능으로 일반화하지 않는다.

## 금지되는 주장

- 임상적으로 검증된 진단 또는 독립적 clinical decision
- NSR/CHF/ARR/AF 네 질환의 확진
- physical AFE PCB, ADC silicon, fabricated SoC, transistor/post-layout 또는 silicon-proven 결과
- live electrode acquisition
- board 36/36을 근거로 한 100% classification accuracy
- 상용 의료 제품에 대한 clinical superiority
- 현재 dataset으로 clinical generalization이 증명됐다는 주장
- 32.912687배를 measured board 또는 전체 system speedup으로 표현하는 문장
- 54.012600 ms를 live ECG 최종 판정시간으로 표현하는 문장
- 0.099 W와 0.005347247400 J를 physical board 측정값으로 표현하는 문장

## 데이터 한계

Strict record-wise split은 같은 source record의 직접 leakage를 막지만 database-class confounding을 제거하지 않는다. 네 class가 서로 다른 DB에 결합돼 있으므로 acquisition, lead, amplitude scale, noise, preprocessing와 record distribution 차이가 classification에 기여했을 수 있다. 이 한계는 generalization 해석에 영향을 주지만 RTL correctness, bit-exact equivalence, IP packaging, board replay와 implementation-resource evidence 자체를 무효화하지 않는다.

## Analog/physical 한계

MATLAB은 nominal pre-validation, LTspice는 실제 schematic 기반 회로 검증, SystemVerilog XMODEL은 model-based non-ideal/RTL handoff verification이다. LTspice에 실제 `.asc`와 netlist가 존재하더라도 세 단계 모두 실제 electrode-to-PCB measurement, transistor-level sign-off, ADC silicon 또는 fabricated chip의 증거가 아니다. 보고서에서도 `schematic/behavioral model-based AFE verification`과 `digital accelerator IP prototype`을 분리한다.

## Benchmark 경계

Accelerator-benefit package는 digital `main` commit `09e4d840...`에서 반입하였다. 보고 가능한 대표 비교는 measured Exact C++ 1,777.699800 ms와 cycle-derived FPGA core 54.012600 ms의 32.912687배 비율이다. Physical board timing·power·energy는 `PENDING_BOARD`이며 zero로 해석하지 않는다.
