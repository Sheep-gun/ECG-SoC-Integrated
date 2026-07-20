# 기여와 차별성

## 1. 네 class 장시간 ECG engineering target

본 연구는 짧은 단일 strip의 binary AF-versus-sinus 출력에 머물지 않고, 장시간 public ECG stream에서 NSR/CHF/ARR/AF 네 class를 다룬다. 이는 임상적·상업적 우월성 주장이 아니라, 더 넓은 engineering classification target을 투명한 hardware architecture로 정의한 기여이다.

## 2. 60초 Snapshot + 30분 Final Membrane

핵심 차별점은 sample/beat evidence를 곧바로 한 번의 class로 치환하지 않고 두 시간축으로 누적하는 구조이다.

- signed 12-bit sample stream에서 beat timing, RR variability, slope/morphology, R-peak amplitude, ectopic-like pair, QRS-related event를 추출한다.
- 60초마다 local class state를 Snapshot Readout으로 요약한다.
- 30개 Snapshot의 signed evidence를 Final Membrane에 누적한다.
- 마지막 WTA가 30분 window의 class를 결정한다.

이 구조는 event와 membrane-like state를 시간에 따라 갱신하므로 `SNN-inspired event/state architecture`로 표현한다. 학습형 deep SNN, spike-timing-dependent learning 또는 생물학적 신경계 등가를 주장하지 않는다.

## 3. RTL-friendly streaming realization

데이터패스는 floating-point 연산이나 전체-window raw buffer 대신 integer counter, comparator, signed accumulator와 fixed-size state를 사용한다. 입력은 sample-by-sample 처리되며 1,800,000개 sample 전체를 메모리에 보관한 뒤 추론할 필요가 없다 [CLM-023]. 이 `avoided full raw-input window storage`는 21,600,000 bit=2,700,000 byte≈2.7 MB decimal이다. Direct RTL 근거와 unresolved aggregate-width 경계는 `STREAMING_STATE_MEMORY_KR.md` 및 `streaming_state_inventory.csv`에 있다.

## 4. mixed-signal-to-digital verification chain

MATLAB은 nominal AFE/ADC intent, headroom, coding과 reference vector를 담당한다. LTspice는 이를 실제 schematic, 전원, S/H와 ADC mapping으로 구현해 35개 nominal/stress run으로 검증한다. XMODEL은 LTspice로 확인한 회로 계약의 SystemVerilog 실행, non-ideal/stress와 long-stream generation을 담당한다. 동일한 10초 10,000표본 LTspice–XMODEL ADC 비교는 MAE 0.6445 LSB, correlation 0.999518, ±5 LSB 98.74%, ±10 LSB 99.89%였다. AFE-generated 36개 final-test chunk는 digital board-replay input과 SHA256 36/36 동일했고, canonical `sample_gap_cycles=2`에서 locked full-top RTL의 final_pred와 final_mem이 각각 36/36 bit-exact였다.

이 결과는 model-based analog intent에서 digital classifier까지의 handoff가 같은 byte stream과 같은 output state로 이어졌다는 integration evidence다. Physical AFE나 silicon validation을 뜻하지 않는다.

## 5. complete digital IP validation chain

Locked Python integer reference, full-top RTL/XSim, Vivado implementation, AXI/IP-XACT packaging, Vitis/MicroBlaze system과 FPGA replay가 하나의 chain으로 연결된다. Pure RTL은 9719 LUT, 5038 FF, 0 BRAM, 0 DSP로 구현됐고 WNS는 8.184 ns였다. Board replay는 final_pred/final_mem 36/36 functional equivalence를 보였다.

Classification accuracy는 별도로 29/36=80.56%이며 hardware equivalence와 혼동하지 않는다.

## 6. reproducible evidence and claim control

세 upstream을 고정 commit의 curated technical snapshot으로 가져오고 모든 retained imported file에 SHA256을 기록했다. 생략한 upstream path는 exclusion registry에 기록하며, PhysioNet raw data는 fixed-version manifest와 expected hashes로 복원한다. Strict source-record-wise split, locked final-test, owner matrix, global metric registry와 SAFE/CAREFUL/FORBIDDEN claim registry를 함께 제공한다. 성능 수치뿐 아니라 말할 수 없는 범위까지 source of truth로 만드는 것이 향후 보고서의 재현성과 심사 방어력을 높인다.

## 차별성의 우선순위

1. 장시간 네 class ECG 문제 정의
2. Snapshot/Final Membrane 다중 시간축 구조
3. 정수형 event/state streaming realization
4. MATLAB–LTspice–XMODEL–digital handoff와 정량 정합·bit identity
5. RTL/IP/FPGA 구현 완결성
6. resource, timing과 완료된 NO_BOARD accelerator benefit benchmark; physical board timing·power는 향후 검증

즉 속도는 지원 증거이며 본 연구의 주된 novelty가 아니다.
