# 문제 정의

## 입력과 출력

입력은 공개 ECG record에서 생성한 1 kSPS, signed 12-bit two's-complement sample stream이다. 출력은 30분 window당 NSR, CHF, ARR, AFF 가운데 하나의 public-dataset class와 네 class의 Final Membrane state이다.

이 네 출력은 네 가지 질병의 임상 진단을 뜻하지 않는다. NSR은 정상 동율동 label이고, ARR은 넓은 부정맥 label이며, CHF는 chfdb에서 가져온 engineering-evaluation label이다. 따라서 문제는 “네 질환을 확진”하는 것이 아니라 “현재 공개 데이터 구성에서 네 ECG class를 분류”하는 것이다.

## 장시간 분류 문제

한 개 30분 decision window는 1,800,000 samples로 구성된다. 필요한 evidence는 서로 다른 시간척도에 존재한다.

- sample/beat 수준: slope, beat timing, QRS 관련 event, R-peak amplitude
- 60초 수준: 국소 rhythm·morphology evidence의 Snapshot state/readout
- 30분 수준: 30개 Snapshot에 걸친 persistence와 recurrence의 Final Membrane accumulation

핵심 설계 문제는 전체 raw window buffer와 floating-point inference에 의존하지 않으면서 이 시간 계층을 정수 counter, comparator, signed accumulator와 fixed-size state로 실현하는 것이다.

## 검증 문제

분류 알고리즘만 맞는 것으로는 semiconductor IP의 완성도를 설명할 수 없다. 다음 경계가 모두 보존돼야 한다.

1. MATLAB nominal AFE/ADC intent와 signed coding convention
2. XMODEL non-ideal/stress 범위와 long signed stream
3. AFE-generated chunk와 digital input의 byte identity
4. Python integer reference와 full-top RTL output
5. Vivado implementation과 IP-XACT packaging
6. MicroBlaze/FPGA replay와 expected output equivalence

여기서 36/36 hardware functional equivalence는 구현 재현성이고, 29/36 classification accuracy는 label correctness이다. 두 값을 합쳐 100% 정확도라고 주장할 수 없다.

## 과학적 해석 문제

Strict source-record-wise split은 동일 source record가 train/validation/final-test에 중복되는 직접 leakage를 방지한다. 그러나 각 class가 서로 다른 DB와 결합돼 있어 acquisition domain과 class identity를 완전히 분리하지 못한다. 따라서 현 accuracy는 현 public-dataset composition에서의 engineering result이며 clinical generalization proof가 아니다.
