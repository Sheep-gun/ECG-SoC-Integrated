# 한계와 claim 경계

## 허용되는 핵심 주장

- Holter-oriented long-window, multi-timescale, SNN-inspired ECG classification architecture
- 1 kSPS signed 12-bit stream과 60초 Snapshot/30분 Final Membrane 구조
- locked final-test chunk 29/36=80.56%, record-majority 16/19=84.21%
- pure RTL resource/timing closure와 packaged IP/FPGA replay
- board final_pred/final_mem 36/36 functional equivalence
- AFE input SHA256 36/36와 canonical cadence AFE-to-RTL 36/36 reproduction
- MATLAB/XMODEL 기반 model-based AFE/ADC verification

## 주의해서 표현할 주장

`Holter-oriented`는 장시간 ECG 구조의 설계 동기를 뜻하며 임상 Holter 인증이 아니다. `SNN-inspired`는 event/state와 membrane-like accumulation을 뜻하며 trained deep SNN이나 생물학적 등가가 아니다. `low-resource`는 0 BRAM/0 DSP와 구현 자원으로 범위를 한정하며, energy superiority는 benchmark 전까지 주장하지 않는다.

Analog robustness는 XMODEL stress와 representative regression이 지원하는 model-based 범위로만 쓴다. R/C mismatch의 30분 final_pred stability는 직접 전체 sweep이 아니라 equivalence-based argument임을 유지한다. 60 Hz target 결과를 50 Hz 환경 성능으로 일반화하지 않는다.

## 금지되는 주장

- 임상적으로 검증된 진단 또는 독립적 clinical decision
- NSR/CHF/ARR/AFF 네 질환의 확진
- physical AFE PCB, ADC silicon, fabricated SoC, transistor/post-layout 또는 silicon-proven 결과
- live electrode acquisition
- board 36/36을 근거로 한 100% classification accuracy
- 상용 의료 제품에 대한 clinical superiority
- 현재 dataset으로 clinical generalization이 증명됐다는 주장
- benchmark 미완료 상태의 latency, throughput, speedup, power, energy 결론

## 데이터 한계

Strict record-wise split은 같은 source record의 직접 leakage를 막지만 database-class confounding을 제거하지 않는다. 네 class가 서로 다른 DB에 결합돼 있으므로 acquisition, lead, amplitude scale, noise, preprocessing와 record distribution 차이가 classification에 기여했을 수 있다. 이 한계는 generalization 해석에 영향을 주지만 RTL correctness, bit-exact equivalence, IP packaging, board replay와 implementation-resource evidence 자체를 무효화하지 않는다.

## Analog/physical 한계

MATLAB은 nominal pre-validation이고 SystemVerilog XMODEL은 model-based non-ideal verification이다. 둘 다 실제 electrode-to-PCB measurement, transistor-level sign-off, ADC silicon 또는 fabricated chip의 증거가 아니다. 보고서 제목과 diagram에서도 `model-based AFE/XMODEL verification`과 `digital accelerator IP prototype`을 분리한다.

## Benchmark 경계

별도 작업의 accelerator-benefit package가 commit, input hash, 측정 범위, measured/cycle-derived/estimated 구분과 result CSV를 갖춘 뒤에만 benchmark claim을 가져온다. 현재 모든 benchmark metric은 `null`이며 zero로 해석하지 않는다.
