# System Architecture

## 전체 구조

![Final system architecture](../reports/final/figures/final_system_architecture.png)

```mermaid
flowchart LR
    A["Public digitized ECG record"] --> B["vin_v = code / 200000"]
    B --> C["PWL-equivalent vin"]
    C --> D["MATLAB AFE pre-design"]
    D --> E["LTspice schematic verification"]
    E --> F["SystemVerilog AFE+ADC XMODEL"]
    F --> G["Signed 12-bit ECG stream"]
    G --> H["60 s Snapshot SNN Readout"]
    H --> I["30 min Final Membrane Readout"]
    I --> J["NSR / CHF / ARR / AFF"]
```

전체 merged-paper 시스템은 public ECG record에서 시작하지만, 이를 raw analog acquisition으로 주장하지 않는다. Upstream MATLAB이 analog-equivalent `vin`과 nominal AFE 사양을 정하고, LTspice가 이를 실제 schematic으로 구현·검증한 뒤, SystemVerilog XMODEL이 mixed-signal/RTL simulation용 signed 12-bit stream을 생성한다.

이 repo의 소유 범위는 signed 12-bit stream 경계부터 시작하는 fully streaming digital path이다. 60초 Snapshot Readout이 ECG evidence를 만들고, 30개 snapshot을 Final Membrane Readout이 누적하여 30분 단위 final class를 출력한다.

## Upstream AFE Dependency and Digital Input Handoff

| 범위 | 역할 | 소유 위치 |
|---|---|---|
| MATLAB AFE+ADC nominal pre-validation | Filter, gain, ADC nominal behavior와 analog-chain intent 확인 | MATLAB teammate repo |
| LTspice XMODEL-aligned schematic verification | ±1.65 V 실제 R/C/op-amp, AC/transient/S&H/ADC/stress 검증 | LTspice teammate workspace, evidence mirrored here |
| AFE+ADC SystemVerilog XMODEL verification | `vin` reconstruction, stress verification, signed 12-bit stream 생성 | XMODEL teammate repo |
| Digital input contract | signed 12-bit, 1 kSPS stream을 RTL/IP에 전달 | Cross-repo handoff boundary |
| SNN accelerator validation | Snapshot/Final Membrane RTL, XSim, Vivado, IP-XACT, Vitis/board replay | This digital repo |

Upstream analog chain은 `HPF 0.482 Hz -> IA x201 -> 60 Hz active Twin-T notch -> LPF 150 Hz -> 12-bit ADC`로 연결된다. 동일 10초 ECG의 LTspice-XMODEL 10,000-code 비교는 98.74%가 ±5 LSB, 99.89%가 ±10 LSB 이내였고 correlation 0.999518, lag 0, clipping 0이었다. 상세 회로·정량표·그림은 [`reports/final/analog_validation_result.md`](../reports/final/analog_validation_result.md)에 보존한다. 이 repo의 디지털 구현 경계는 signed 12-bit stream 이후이며, locked RTL/IP/FPGA 동작은 별도로 검증한다.

## Snapshot-to-Final Pipeline

![Snapshot-to-final membrane pipeline](../reports/final/figures/snapshot_to_final_membrane_pipeline.png)

Snapshot Readout은 ECG stream을 다음 evidence로 압축한다.

| Evidence | RTL block | 직관적 역할 |
|---|---|---|
| Beat/QRS | `ecg_event_encoder_adaptive.v`, `qrs_lif_detector.v` | slope event를 누적해 beat spike 생성 |
| Rhythm prediction | `pnn_rhythm_predictor.v` | 직전 RR winner가 다음 beat를 예측했는지 판단 |
| Variability | `rdm_variability_neuron.v` | 연속 RR interval 변화량을 threshold bank로 측정 |
| Morphology complexity | `dscr_spike_counter.v`, `qrs_maf_neuron.v` | slope sign flip, QRS width, energy, pre-QRS bump 측정 |
| Amplitude | `ram_peak_accumulator.v` | R-peak amplitude response를 integer code로 변환 |
| Ectopic pair | `ectopic_pair_neuron.v` | early/late RR pair pattern 감지 |
| Terminal delay proxy | `rbbb_qrs_delay_bank.v` | wide QRS와 terminal activity 반복 여부 감지 |

Final Membrane Readout은 snapshot WTA 결과만 단순 투표하지 않는다. Snapshot winner와 evidence counter를 class별 signed membrane에 누적하고, guarded/silent AFF/rescue/boost 조건을 통해 30분 evidence를 반영한다.

## Accelerator IP Core 관점

본 설계가 accelerator IP Core로 볼 수 있는 이유는 ECG long-window classification workload를 전용 RTL datapath로 고정했기 때문이다. 입력 stream, control/status, final output, done/irq, profile counter가 명확하며, AXI4-Lite control과 AXI4-Stream input을 갖는 IP-XACT package로 정리되어 있다.

| 항목 | 의미 |
|---|---|
| Input | AFE+ADC XMODEL 이후 signed 12-bit ECG stream |
| Datapath | event/spike extraction, class membrane accumulation, WTA |
| IP packaging | `ip_repo/snn_ecg_axi_accelerator/component.xml` |
| Feeder IP | `ip_repo/axi_lite_axis_sample_feeder/component.xml` |
| Board integration | Vitis/MicroBlaze full-record replay |
