# 설계 기여와 차별성

## 문제 설정

장시간 ECG에서 질환 관련 특징은 모든 시간에 지속되지 않고 일부 구간에서만 강하게 나타날 수 있다. 한편 원시 ECG 전체를 저장하고 dense model로 반복 처리하는 방식은 wearable edge IP에 메모리·연산 부담을 준다.

## 주요 기여

1. **Window-to-record multi-timescale accumulation**
   60초마다 리듬·파형 evidence를 Snapshot Membrane으로 요약하고, 30개 Snapshot의 강도, 빈도, 반복성과 지속성을 Final Membrane에 누적해 한 30분 입력을 분류한다.

2. **해석 가능한 domain-specific evidence**
   학습된 latent tensor 대신 PNN, RDM, Ectopic Evidence, DSCR, RAM, QRS MAF와 RBBB-like를 정수 evidence로 사용한다. 어떤 사건이 class membrane에 영향을 주었는지 RTL 내부 상태로 추적할 수 있다.

3. **streaming hardware mapping**
   comparator, counter, shift/add, signed accumulator와 exact lookup 중심으로 sample-by-sample 상태를 갱신한다. 최종 Pure RTL은 BRAM 0, DSP 0으로 구현됐다.

4. **analog-to-FPGA traceability**
   digitized ECG의 PWL 재구성부터 MATLAB, LTspice, XMODEL, Python/Exact C++, RTL/XSim, AXI IP, MicroBlaze와 FPGA replay까지 동일 stream contract와 locked output을 연결했다.

5. **개발 과정의 timing closure**
   RDM-to-prediction critical path를 관측하고 pipeline으로 구조 분할한 뒤, timing을 재검증하고 Python/RTL/FPGA equivalence를 확인했다.

## 선행연구 대비 거시적 차이

개별 beat SNN은 “이 박동이 어떤 유형인가”를, event-driven anomaly detector는 “지금 이상이 있는가”를 주로 출력한다. software CNN/LSTM과 24시간 Transformer는 기록 수준 통합을 수행하지만 dense feature와 software inference가 중심이다. 본 설계는 장시간 구간 evidence를 명시적 membrane state로 누적해 NSR, CHF, ARR, AF를 출력하고 이를 RTL/IP/FPGA로 구현한다.

검토한 대표 연구 범위에서는 NSR·CHF·ARR·AF 입력 분류, Snapshot evidence 상태화, 장시간 누적, RTL/IP/FPGA 구현과 MATLAB–XMODEL–RTL 추적성을 함께 적용한 사례를 확인하지 못했다. 이는 세계 최초나 문헌 전체에 동일 연구가 없다는 단정이 아니다.
