# 참가신청서 (4) 설계회로 검증 — 디지털 및 통합 검증 초안

## 2. 디지털 회로 검증

디지털 회로는 결과값만 확인하지 않고, **기준 모델 일치 → 내부 연산 일치 → 전체 제어 흐름 → IP 인터페이스**의 네 단계로 검증하였다.

### 2-1. Python 정수 기준 모델–RTL 최종 출력 검증

설계가 고정된 Python 정수 기준 모델을 Golden Reference로 사용하였다. 동일한 36개 시험 입력을 Python과 RTL/XSim에 넣고 최종 분류값 36개와 클래스별 Final Membrane 144개를 비교한 결과, 모든 값이 일치하였다. 이는 RTL이 기준 알고리즘의 최종 계산 결과를 손실 없이 재현함을 의미한다.

### 2-2. Exact C++–RTL 내부 연산 상태 검증

독립적으로 작성한 Exact C++ 모델을 이용하여 고정폭 산술, 모듈 microtrace, sample 처리 상태, Snapshot 경계 및 최종 상태를 단계별로 비교하였다. 고정폭 연산 793,595건, 내부 상태 hash 240,000건, Snapshot 경계 1,080건, 최종 분류 36건 및 Final Membrane 144건에서 불일치가 없었다. 따라서 최종값이 우연히 같은 것이 아니라 중간 계산 과정도 동일함을 확인하였다.

### 2-3. Full-top 제어 흐름 검증

36개 30분 입력을 Full-top RTL/XSim에 각각 인가하였다. 모든 case에서 1,800,000개 sample이 수락되고, 60초 단위 Snapshot 30개가 생성된 뒤 최종 판단 1회와 `final_valid`가 발생하였다. 이 결과는 긴 입력 구간의 sample 수집, Snapshot 누적, 최종 판단 순서가 설계 의도대로 동작함을 보여준다.

### 2-4. AXI/IP 패키징 및 인터페이스 검증

Vivado 2020.2 XSim에서 패키징된 accelerator IP와 sample-feeder IP를 다시 컴파일하고 smoke test를 실행하였다. AXI-Lite read/write, AW/W 도착순서 변화, read backpressure 중 데이터 유지, AXI-Stream `TVALID/TREADY` backpressure, 마지막 sample의 `TLAST`, 상태·오류·계수기 register, 완료 및 IRQ 동작을 확인하였으며 두 testbench 모두 PASS하였다.

권장 배치:

- 검증 순서: `figures/final/VAL-02_digital_validation_flow.svg`
- 2-1·2-2 결과: `figures/final/VAL-02A_multilevel_digital_equivalence.svg`
- 2-3 결과: `figures/final/VAL-02B_fulltop_control_timeline.svg`
- 2-4 결과: `figures/final/VAL-02C_axi_ip_protocol_waveform.svg`
- 정량 결과표: `tables/section4_digital_validation_summary.md`

## 3. 아날로그–디지털 통합 검증

XMODEL AFE·ADC가 생성한 signed 12-bit, 1 kSPS 출력이 디지털 RTL 입력까지 동일하게 전달되는지 먼저 SHA-256으로 확인하였다. 36개 30분 입력 모두에서 전달 전후 byte stream이 일치하였다. 이어서 동일 stream을 RTL/XSim에 인가한 결과, 모든 case에서 1,800,000개 sample 수락, Snapshot 30개, 최종 판단 1회를 확인하였다. 최종 분류값과 네 클래스 Final Membrane도 36개 case 모두 기준 결과와 일치하였다.

권장 배치:

- 검증 순서: `figures/final/VAL-03_analog_digital_integration_flow.svg`
- 정량 결과표: `tables/section4_integration_validation_summary.md`

분류 정확도 29/36(80.56%)와 Confusion Matrix는 회로가 기준 연산을 정확히 재현했는지를 보여주는 위 검증 결과와 목적이 다르므로, (5) 설계회로 구현결과의 시스템 성능 항목에 배치한다.
