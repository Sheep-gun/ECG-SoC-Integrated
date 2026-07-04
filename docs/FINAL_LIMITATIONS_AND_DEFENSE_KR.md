# Final Limitations and Defense

## 1. 최종 한계 요약

| 한계 | 현재 상태 |
|---|---|
| raw analog ECG acquisition | 수행하지 않음. source는 공개 digitized ECG record |
| physical DAC replay | 수행하지 않음. virtual DAC / PWL-equivalent reconstruction |
| physical AFE PCB / ADC silicon | 측정하지 않음 |
| Virtuoso layout/post-layout | 수행하지 않음 |
| clinical validation | 수행하지 않음. engineering prototype |
| strict record-wise final accuracy | 아직 아님. chunk-level 결과와 record-wise stress-test를 분리 |
| full dataset board replay | 아직 아님. test NSR case 0 한 건 full-record replay 완료 |
| board power measurement | 아직 아님. Vivado estimate만 존재 |

## 2. 예상 질문과 답변

### Q1. 원본 ECG가 이미 디지털인데 AFE+ADC를 다시 거치는 게 의미 있나?

의미는 “raw analog를 새로 측정했다”가 아니라, digital ECG record를 physical-voltage-equivalent input으로 재해석하고 AFE+ADC 이후 digital stream이 accelerator에 들어가는 전체 flow를 검증한다는 데 있다. 공개 ECG dataset은 대부분 digitized record이므로, 본 프로젝트는 virtual DAC/PWL-equivalent `vin` reconstruction과 nominal AFE+ADC XMODEL을 통해 model-based mixed-signal-to-digital verification을 구성했다.

### Q2. 이것이 실제 raw analog ECG 복원인가?

아니다. `vin_v = signed_code / 200000` 기반의 analog-equivalent/PWL-equivalent waveform reconstruction이다. 실제 환자 전극에서 측정한 raw analog waveform을 복원했다고 주장하지 않는다.

### Q3. 실제 AFE PCB나 CMOS post-layout 검증을 했나?

아니다. HPF, IA gain x201, 60 Hz notch, LPF 150 Hz, 12-bit ADC quantization을 갖는 nominal AFE+ADC XMODEL/evidence figure를 사용했다. PCB 측정, ADC silicon measurement, Virtuoso post-layout verification은 향후 과제이다.

### Q4. dataset leakage 문제는 없나?

현재 chunk-level balanced split에는 source record overlap이 있다. audit 결과 136 chunks, 70 class-record pairs 중 33 class-record pairs가 여러 split에 걸쳐 있다. 그래서 32/36 = 88.89% test accuracy를 strict record-wise generalization으로 주장하지 않는다.

### Q5. 88.89%는 strict record-wise인가?

아니다. 88.89%는 30분 chunk-level balanced test split 기준이다. 보조 audit으로 frozen rule set의 record-wise regrouping stress test `30/35 = 85.71%`와 LORO recall NSR/CHF/ARR/AFF `94.12% / 94.12% / 88.24% / 91.18%`를 제시한다. publishable strict record-wise claim은 protocol을 먼저 고정한 뒤 model/rule search를 다시 수행해야 한다.

### Q6. 이게 임상적으로 유효한가?

임상적으로 유효하다고 주장하지 않는다. 본 프로젝트는 FPGA/VLSI engineering prototype이다. clinical validation, patient-level prospective study, regulatory validation은 수행하지 않았다.

### Q7. 왜 Accelerator IP Core라고 부를 수 있나?

ECG stream 처리와 long-window classification workload를 전용 RTL datapath로 고정했고, AXI wrapper, AXI4-Lite register, AXI4-Stream sample input, sample feeder, IP-XACT `component.xml`, xgui, Vivado timing/resource report를 갖는다. MicroBlaze에서 packaged IP를 호출하는 system smoke와 full-record board replay도 수행했다.

### Q8. 실제 FPGA board에서 돌렸나?

그렇다. 두 수준의 board evidence가 있다.

| 단계 | 결과 |
|---|---|
| MicroBlaze smoke | 16 samples / 2 snapshots, UART `SNN_ECG_MB_SMOKE_PASS` |
| Full-record replay | test NSR case 0, 1,800,000 samples, UART `SNN_ECG_FULL_REPLAY_BOARD_PASS` |

Full-record replay transcript는 `reports/board_replay/transcripts/test_case0_nsr_uart_full_replay.txt`에 있다.

### Q9. full-record board replay와 smoke test 차이는 무엇인가?

Smoke는 IP 연결, register map, feeder, interrupt, final readback을 빠르게 확인하기 위한 16-sample deterministic test이다. Full-record replay는 실제 30분 ECG `.mem` 1,800,000 samples를 board에 보내고, 30 snapshots와 final decision이 Python/XSim expected와 일치하는지 확인한다.

### Q10. 이화여대/UNIST/SWIR 수상작과 비교해 강점과 약점은 무엇인가?

| 비교 대상 | 강점 | 약점 |
|---|---|---|
| 이화여대 biomedical CMOS hybrid system | digital RTL/IP packaging/Vitis board replay evidence가 강함 | physical analog CMOS/post-layout evidence는 약함 |
| UNIST GNN force-field accelerator IP | low-resource biomedical streaming IP로 차별화 | workload scale/HBM/large accelerator 성격은 약함 |
| SWIR 2-step SS-ADC | AFE+ADC model과 digital accelerator 연결 flow를 제시 | actual ADC circuit/silicon proof는 없음 |
| Scara Wafer Vision | FPGA/VLSI IP 설계 purity가 높음 | 실물 system demo성은 상대적으로 약할 수 있음 |
| WebAssembly/ECDSA/ChaCha20류 IP | 특정 workload를 IP Core로 구현한 성격이 유사 | biomedical dataset/protocol 한계는 별도 방어 필요 |

## 3. 제출용 안전 표현

사용해도 되는 표현:

- analog-equivalent `vin` reconstruction
- PWL-equivalent waveform
- AFE+ADC XMODEL
- model-based mixed-signal-to-digital verification
- engineering validation
- board-level integration replay
- chunk-level test accuracy
- record-wise stress-test
- SNN-inspired ECG Classification Accelerator IP Core

피해야 하는 표현:

- raw analog ECG recovered
- actual electrode acquisition
- actual AFE PCB verified
- silicon ADC measured
- Virtuoso post-layout verified
- clinical validation
- strict record-wise verified
- full dataset board replay completed

## 4. 최종 방어 문장

> 본 프로젝트는 실제 전극 기반 의료기기 검증이 아니라, 공개 digitized ECG record를 analog-equivalent 입력으로 재구성하고 AFE+ADC XMODEL을 통과시킨 signed 12-bit stream을 SNN-inspired Accelerator IP Core에 입력하는 FPGA/VLSI engineering prototype이다. 디지털 IP는 Python golden, XSim, Vivado implementation, AXI/IP packaging, MicroBlaze smoke, 1-case full-record board replay로 검증했다. 임상/physical analog 검증은 향후 과제이다.
