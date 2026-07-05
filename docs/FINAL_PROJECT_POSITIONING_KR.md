# Final Project Positioning

## 1. 한 문장 포지셔닝

본 프로젝트는 실제 전극 기반 의료기기 검증이 아니라, **AFE+ADC XMODEL과 SNN-inspired RTL Accelerator IP Core를 연결한 biomedical mixed-signal-to-digital FPGA prototype**이다.

공개 digitized ECG record를 analog-equivalent `vin`으로 재구성하고, AFE+ADC XMODEL을 통과시켜 생성한 signed 12-bit stream을 실제 RTL/IP에 입력하여 long-record ECG 4-class classification을 수행한다.

## 2. 주장할 수 있는 것

| 주장 가능 | 근거 |
|---|---|
| ECG 4-class Accelerator IP Core | RTL core, AXI wrapper, IP-XACT `component.xml`, xgui, Vivado reports |
| Long-record streaming classifier | 60초 snapshot 30개를 30분 final membrane으로 누적 |
| SNN-inspired event/membrane architecture | event/spike evidence, signed membrane update, WTA decision |
| Python/XSim bit-accurate RTL validation | locked final_test final prediction/membrane mismatch 0/36 |
| Low-resource digital classifier core | board wrapper BRAM 0 / DSP 0, AXI OOC BRAM 0 / DSP 0 |
| Model-based AFE+ADC integration | `vin_v = signed_code / 200000`, HPF/gain/notch/LPF/ADC nominal model figures |
| Board-level IP call | MicroBlaze smoke UART PASS transcript, XSDB MMIO transcript |
| Locked board integration replay | MicroBlaze full-record bitstream/XSA/ELF rebuilt, class-wise UART replay executed with final_pred/final_mem 4/4 exact match |

## 3. 주장하면 안 되는 것

| 주장 금지 | 이유 |
|---|---|
| raw analog ECG acquisition | source DB는 already digitized record |
| raw analog ECG reconstruction completed | PWL-equivalent reconstruction이지 원래 analog waveform 복원이 아님 |
| physical DAC replay | PC/UART digital `.mem` replay만 수행 |
| actual ECG electrode measurement | 전극/환자/실측 환경 없음 |
| physical AFE PCB validation | PCB 측정 없음 |
| silicon ADC measured | ADC silicon 측정 없음 |
| Virtuoso post-layout verification completed | layout/post-layout simulation 없음 |
| clinical diagnosis validation | engineering prototype이며 임상 validation 아님 |
| full final_test batch board replay completed | class-wise representative replay만 수행했고 전체 final_test batch는 아직 아님 |

## 4. 심사 방어 논리

### 왜 이미 digitized ECG에 AFE+ADC XMODEL을 붙였나?

공개 ECG dataset은 대부분 digital record로 제공된다. 본 프로젝트는 이를 실제 analog acquisition으로 과장하지 않고, digital code를 analog-equivalent `vin` input으로 재해석하여 AFE+ADC nominal model을 통과시키는 verification stage를 구성했다. 목적은 analog PCB 성능을 주장하는 것이 아니라, **mixed-signal front-end 이후 생성될 signed 12-bit stream이 digital accelerator로 연결되는 흐름**을 검증하는 것이다.

### 왜 Accelerator IP Core인가?

범용 CPU software classifier가 아니라, ECG stream 처리와 class evidence accumulation을 RTL datapath로 고정했다. AXI4-Lite control/status, AXI4-Stream sample input, sample feeder, IP-XACT packaging 산출물이 있으며, locked model 기준 MicroBlaze full-record replay bitstream/XSA/ELF build와 class-wise UART board replay를 수행했다.

### board full replay와 smoke의 차이는 무엇인가?

Smoke는 16 samples / 2 snapshots로 register map, feeder, interrupt, final readback을 빠르게 확인한다. Full replay는 1 kSPS x 30분 = 1,800,000 samples를 실제 board에서 입력하고, 30 snapshots와 final decision을 locked full-top XSim expected와 비교하는 단계이다. 현재 NSR/CHF/ARR/AFF 각 1건 transcript가 생성되어 있고 final_pred와 final_mem이 4/4 일치한다.

### 최종 성능을 어떻게 표현해야 하나?


## 5. 최종 제출용 안전 문장

> 본 프로젝트는 공개 digitized ECG record를 analog-equivalent `vin`으로 재구성하고, AFE+ADC XMODEL을 통과시켜 signed 12-bit stream을 생성한 뒤, SNN-inspired ECG Classification Accelerator IP Core에 입력하여 30분 long-record NSR/CHF/ARR/AFF classification을 수행하는 FPGA/VLSI engineering prototype이다. 디지털 IP는 Python golden, locked Final Membrane XSim, Vivado implementation, AXI/IP packaging, Vitis/MicroBlaze bitstream/XSA/ELF build를 통해 검증했다. 단, physical AFE/ADC 실측이나 의료 유효성 검증은 수행하지 않았다.
