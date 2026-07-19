# ECG-SoC: 웨어러블 심전도 부정맥 감지 Mixed-Signal SoC

> 제27회 대한민국 반도체설계대전 · 한양대학교 융합전자공학부

---

## 프로젝트 개요

공개 digitized ECG record를 **analog-equivalent 신호로 재구성**해 팀 설계 **AFE+ADC XMODEL**에 통과시켜 **1 kSPS signed 12-bit stream**을 만들고, 이를 **SNN-inspired 가속기 IP Core**에 입력하여 **NSR/CHF/ARR/AFF 4클래스**를 분류하는 FPGA/VLSI engineering prototype입니다.

LTspice 회로 설계 + XModel(Questa) 통합 검증 + FPGA(Nexys A7) board replay로 검증한 **model-based mixed-signal-to-digital ECG accelerator**입니다. (물리 전극 실측/AFE PCB/CMOS layout·clinical 검증은 범위 밖 — 아래 한계 참조)

> 📂 구조·데이터·결과 전체: **[PROJECT_LAYOUT.md](PROJECT_LAYOUT.md)** · 디지털 블록: **[docs/DIGITAL_BLOCK.md](docs/DIGITAL_BLOCK.md)** · ADC 결정: **[docs/AFE_ADC_XADC_decision.md](docs/AFE_ADC_XADC_decision.md)**

---

## 시스템 흐름

```
공개 digitized ECG record
  → analog-equivalent vin 재구성 (code / 200000, 선형보간 1kSPS)
  → AFE+ADC XMODEL : HPF 0.48Hz · IA ×201 · 60Hz notch(Q≈5) · LPF 150Hz · 12-bit ADC(±1.65V)
  → 1 kSPS signed 12-bit stream (.mem)
  → 60초 Snapshot SNN Readout   (event / rhythm / morphology / variability evidence)
  → 30분 Final Membrane Readout (30 snapshot signed 누적, WTA)
  → NSR / CHF / ARR / AFF
```

## 분류 대상 — 4클래스 ECG

| 클래스 | 명칭 | 핵심 특징 | 원본 DB |
|---|---|---|---|
| NSR | 정상 심전도 | 규칙적 RR, 정상 QRS | nsrdb (~24h) |
| CHF | 울혈성 심부전 | QRS 폭 증가, 전압 감소 | chfdb (~20h) |
| ARR | 부정맥 계열 | 조기수축, 이상 박동 | mitdb (30분 excerpt) |
| AFF | 심방세동 | RR 완전 불규칙 | afdb (~10h) |

---

## 팀 구성 및 역할

| 팀원 | 역할 | 자료 |
|---|---|---|
| 양건 (팀장) | 디지털 SNN accelerator / RTL / Vivado / Vitis / FPGA·IP packaging | `digital_block/` · [SNN-ECG-4-Class-Classifier](https://github.com/Sheep-gun/SNN-ECG-4-Class-Classifier) |
| 서민우 | MATLAB AFE+ADC nominal pre-validation / reference vector generation | `matlab_afe_validation/` |
| 이수환 | SystemVerilog XMODEL AFE+ADC verification / mixed-signal-to-digital integration | `analog/`, `docs/`, `datasets/fullrec_afe*` |

---

## AFE 아날로그 설계 (이수환)

**3-op-amp 계측 증폭기 (IA)** — 전체 이득 `Av = 1 + 2·R_fb/Rg = 201` (R_fb=100kΩ, Rg=1kΩ), CMRR 목표 >100dB (IEC 60601-2-47), 공급 ±1.65V
**HPF** — fc ≈ 0.48Hz (C=33nF, R=10MΩ), baseline/DC 오프셋 제거
**능동 Twin-T Notch** — 60Hz 전원선 간섭 제거, 부트스트랩(Q≈5)으로 통과대역 보존
**LPF** — 150Hz (anti-alias)
**SAR ADC** — 12-bit / 1 kSPS / offset-binary (`code=((Vin+1.65)/3.3)×4095`)

**XModel+Questa 특성 측정** (`make char` / `make pli`)
| 항목 | 목표 | 측정 |
|---|---|---|
| 통과대역 이득 | 201 | ~200 |
| −3dB 대역폭 | 150Hz | 150Hz |
| 60Hz 노치 | 제거 | 80dB |
| CMRR | >100dB | 156dB* |
| 60Hz PLI(1V CM) 잔차 | — | 0.9mV (신호 284mV) |

*모델 이상매칭 가정; 실제는 저항 오차로 제한. XModel 설계 정본 = `analog/ecg_afe_xmodel.sv`, 회로도 = `ECG_AFE_LTspice/ecg_afe.asc`.

> **ADC / FPGA 검증 방식**: 현재 FPGA 검증은 canonical signed 12-bit `.mem` stream을 이용한 **MicroBlaze board replay**이다. **Live XADC-in-loop ECG acquisition은 현재 검증 범위에 포함되지 않는다.** XADC 적용 시에는 SAR/XADC voltage-scale 및 digital threshold 정합에 대한 별도 검증이 필요하다. (커스텀 SAR ADC는 비합성 SoC 설계물로 유지; 스케일 정합 산출 `docs/AFE_ADC_XADC_decision.md`.)

---

## 디지털 SNN Accelerator (양건)

정본: **`digital_block/`** (팀원 저장소 스냅샷) · 상세 개요: **[docs/DIGITAL_BLOCK.md](docs/DIGITAL_BLOCK.md)**

- **60초 Snapshot Readout**: QRS LIF beat 검출 + feature 뉴런(rhythm pNNx, RR variability, morphology, R-peak amplitude, ectopic pair, terminal delay)이 event·counter evidence 생성
- **30분 Final Membrane Readout**: 30개 snapshot을 class별 signed membrane에 누적(guarded/silent/rescue 로직) → WTA로 최종 class
- 정수 datapath (counter/comparator/signed accumulate, **DSP·BRAM 0**)
- **최종모델** `structural_guarded_silent_aff_1008710` — final test(30분 chunk) **80.56%**, record-majority 84.21%
- **HW**: 9,719 LUT / 5,038 FF / 0 DSP (pure RTL) · board replay **36/36 exact**

---

## 통합 및 검증 흐름

```
[1] AFE 특성/PLI      → XModel+Questa  (make char / make pli)
[2] full-record AFE   → datasets/fullrec_afe(59) + fullrec_afe_remaining(68) = DB 전체
[3] AFE → 30분 chunk  → SHA256 36/36 identical to digital board-replay input
[4] AFE → locked RTL  → canonical XSim cadence로 final_pred·final_membrane 36/36 bit-exact
```

두 가지 **36/36**은 의미가 다르므로 분리해서 읽어야 함:

- **Digital board replay** (양건, 디지털 IP 자체 검증)
  - board-facing digital IP replay validation
  - final_pred / final_mem matched digital expected outputs for **36/36** final-test chunks

- **AFE → locked RTL XSim integration** (이수환, mixed-signal 통합 검증)
  - AFE-generated chunks were **SHA256-identical** to board-replay inputs for **36/36** chunks
  - under **canonical board-facing XSim cadence**, final_pred and final_mem reproduced locked digital golden results for **36/36** chunks
  - 상세: **[docs/integration_latest/AFE_latest_locked_model_integration.md](docs/integration_latest/AFE_latest_locked_model_integration.md)** · 검증 요약: **[docs/VALIDATION_STATUS.md](docs/VALIDATION_STATUS.md)**

- AFE 시뮬은 FPGA 보드 불필요(WSL XModel+Questa). 실행: `cd ~/ECG-SoC && make sim`

---

## 한계 (Scope)

공개 데이터는 이미 digitized(raw sensor 아님) · AFE+ADC는 **XMODEL/nominal 모델**(물리 PCB·ADC silicon 아님) · CMOS post-layout·clinical 검증 없음 · 물리 전극/DAC/실측 acquisition 없음. 핵심 주장은 **AFE+ADC XMODEL과 SNN RTL/IP를 연결한 model-based mixed-signal-to-digital FPGA prototype**입니다.

## 기술 스택

LTspice · XModel(Questa) · Vivado / Verilog · Nexys A7-100T (XADC 내장) · Python (wfdb·numpy·scipy)
