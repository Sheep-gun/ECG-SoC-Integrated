# System Architecture

## 전체 구조

```mermaid
flowchart LR
    A["Public digitized ECG record"] --> B["vin_v = code / 200000"]
    B --> C["PWL-equivalent vin"]
    C --> D["AFE+ADC XMODEL"]
    D --> E["Signed 12-bit ECG stream"]
    E --> F["Snapshot SNN Readout"]
    F --> G["Final Membrane Readout"]
    G --> H["NSR / CHF / ARR / AFF"]
```

## AFE+ADC XMODEL 입력 생성

공개 ECG record는 이미 digitized data이므로 원래 analog ECG를 복원하는 것이 아니다. 본 프로젝트는 digitized code를 analog-equivalent `vin`으로 재해석하고, virtual DAC/PWL-equivalent waveform으로 AFE+ADC XMODEL에 입력한다.

| Stage | 설명 |
|---|---|
| `code / 200000` | signed code를 voltage-equivalent input으로 변환 |
| HPF | baseline drift 억제 |
| IA gain x201 | ECG amplitude scaling |
| 60 Hz notch | power-line component suppression |
| LPF 150 Hz | 고주파 noise 제한 |
| 12-bit ADC | RTL 입력 signed 12-bit stream 생성 |

## Digital Accelerator

Digital datapath는 dense MAC 기반 neural network가 아니라 ECG domain evidence를 spike/event로 압축하는 구조이다.

| Block | 역할 |
|---|---|
| Input normalizer/event encoder | sample stream에서 event evidence 생성 |
| QRS/rhythm/morphology evidence | ECG-specific feature spike와 counter 생성 |
| Snapshot Readout | 60초 단위 class/evidence membrane 생성 |
| Final Membrane Readout | 30개 snapshot evidence 누적 |
| WTA | NSR/CHF/ARR/AFF 최종 class 결정 |

## Accelerator IP 관점

본 IP는 ECG stream 처리와 long-window class membrane accumulation을 전용 RTL datapath로 고정한다. AXI4-Lite control/status, AXI4-Stream sample input, IP-XACT packaging, MicroBlaze board replay flow를 갖기 때문에 reusable accelerator IP core로 볼 수 있다.
