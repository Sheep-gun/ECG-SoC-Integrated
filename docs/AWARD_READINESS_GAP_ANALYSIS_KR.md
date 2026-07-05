# 수상권 경쟁력 보강 분석

## 1. 현재 프로젝트의 객관적 위치

본 프로젝트는 **AFE+ADC XMODEL 연동 SNN 기반 장시간 ECG 4-Class Classification Accelerator IP Core 설계**이다. 공개 ECG digitized record를 AFE+ADC 이후의 signed 12-bit stream으로 연결하고, FPGA RTL에서 NSR / CHF / ARR / AFF를 장시간 window로 분류한다.

핵심 강점은 디지털 accelerator IP 관점이다. Python golden과 RTL/XSim 비교가 맞고, Vivado resource/timing, AXI wrapper, IP-XACT packaging, MicroBlaze smoke system, 1-case full-record board replay 산출물이 존재한다. 반면 수상권 경쟁에서 약한 부분은 dataset split 신뢰성, analog physical evidence, full-split board replay batch, baseline/ablation 해석이다.

| 항목 | 현재 상태 | 수상권 대비 평가 |
|---|---|---|
| Digital RTL | 강함. 30분 stream top, snapshot core, final membrane 존재 | 경쟁 가능 |
| Python-vs-RTL 검증 | pred/mem mismatch 0/136 | 강점 |
| Vivado timing/resource | board/OOC/MicroBlaze reports 존재 | 강점 |
| IP packaging | `component.xml`, `xgui`, AXI wrapper, feeder 존재 | 강점 |
| AFE/ADC physical verification | XMODEL/nominal model 중심 | 이화여대/SWIR 대비 약함 |
| Dataset validation | seed 20260808 strict record-wise split, source/physical overlap 0 | 보강됨 |
| Board-level demo | bit/XSA/XSDB smoke 있음, test NSR case 0 full replay PASS | 보강됨. full-split batch는 남음 |
| Baseline comparison | 새로 일부 정리, energy는 추정 | 보강 필요 |

## 2. 수상작별 비교

### 2.1 이화여대 biomedical CMOS hybrid system

- 상대 강점: analog/mixed-signal system 완성도, Cadence/Virtuoso layout/post-layout 계열 검증.
- 본 프로젝트 강점: digital accelerator IP, XSim bit-accurate 검증, AXI/IP packaging.
- 본 프로젝트 약점: 실제 analog layout/post-layout, PCB/silicon measurement가 없다.
- 보강 방향: AFE+ADC XMODEL evidence figure를 명확히 제시하고, physical analog 검증이 아님을 정직하게 적는다.

### 2.2 UNIST GNN force-field accelerator IP

- 상대 강점: workload bottleneck, FPGA/HBM accelerator IP, baseline 대비 성능/throughput 개선.
- 본 프로젝트 강점: 작은 FPGA에서 low-resource biomedical streaming IP라는 명확한 방향, DSP/BRAM 0 accelerator core.
- 본 프로젝트 약점: 대형 workload, HBM, 엄격한 CPU/GPU baseline 대비 speedup/energy 비교가 부족하다.
- 보강 방향: latency/resource/cycle-derived throughput, ablation, 병목 해결 흐름을 표로 정리한다.

### 2.3 SWIR pixel-level 2-step SS-ADC

- 상대 강점: signal acquisition circuit/ADC architecture 자체의 완성도.
- 본 프로젝트 약점: AFE/ADC는 실제 회로 tapeout/measurement가 아니라 XMODEL/nominal behavior 중심이다.
- 보강 방향: XMODEL 입력 재구성, HPF/notch/LPF/ADC quantization figure를 통해 model-based verification 근거를 강화한다.

### 2.4 Scara Wafer Vision

- 상대 강점: 실물 시스템 demo와 응용 완성도.
- 본 프로젝트 강점: 반도체 설계/IP flow와 FPGA 검증.
- 보강 방향: IP catalog evidence, MicroBlaze smoke, UART PASS transcript, board replay plan을 명확히 정리한다.

## 3. 최우선 보강 항목

| 우선순위 | 항목 | 필요한 이유 | 현재 작업 결과 |
|---:|---|---|---|
| 1 | Dataset split audit | 88.89%가 strict record-wise인지 방어 필요 | `reports/award_readiness/dataset_split_audit.md` |
| 2 | Final Membrane 확정 프로토콜 | strict train/validation 선택 및 lock 이후 test 최종 평가 | `DATASET_SPLIT_VALIDATION_KR.md` |
| 3 | AFE+ADC evidence figure | analog/mixed-signal 근거 보강 | `figures/*.png`, `AFE_XMODEL_EVIDENCE_KR.md` |
| 4 | Ablation | 왜 final membrane/evidence가 필요한지 수치화 | `ablation_summary.md` |
| 5 | Baseline metrics | accelerator IP 설득력 강화 | `cpu_vs_rtl_summary.md`, `vivado_metrics.md` |
| 6 | Board/IP evidence | 실물 시스템 완성도 보강 | `BOARD_AND_IP_PACKAGING_EVIDENCE_KR.md` |

## 4. 금지해야 할 과장 표현

다음 표현은 현재 repo evidence로는 금지한다.

- raw analog ECG를 복원했다.
- 실제 환자에게서 ECG를 측정했다.
- 실제 AFE PCB나 ADC 회로를 실측했다.
- Virtuoso post-layout 검증을 완료했다.
- 임상적으로 검증된 진단 시스템이다.
- 88.89%만으로 완료 진단 성능을 주장할 수 있다.
- locked result 없이 strict record-wise 최종 성능을 단정한다.
- 전체 dataset의 모든 full 30분 board replay batch가 완료됐다.

대신 다음처럼 표현한다.

- 공개 digitized ECG를 physical-voltage-equivalent input으로 재구성했다.
- AFE+ADC XMODEL/nominal chain을 통과한 signed 12-bit RTL input flow를 구성했다.
- Python golden과 RTL/XSim bit-accurate 비교를 수행했다.
- 최종 strict record-wise dataset과 Final Membrane lock protocol을 기준으로 결과를 제시한다.

## 5. 최종 보강 체크리스트

- [x] record-wise split audit
- [x] strict record-wise split 구성
- [x] Final Membrane lock/test protocol 정리
- [x] AFE input/output/ADC waveform plot
- [x] HPF/notch/LPF frequency response plot
- [x] final membrane ablation
- [x] final-layer evidence ablation
- [x] CPU/Python final-readout latency baseline
- [x] RTL cycles/sample
- [x] Vivado resource/timing/power estimate collection
- [x] IP-XACT/component.xml evidence
- [x] AXI register/system address evidence
- [ ] raw/AFE-off full-record end-to-end accuracy
- [ ] HPF/notch/LPF-off regenerated dataset accuracy
- [x] full 30분 board replay transcript 1건
- [x] Vitis-built MicroBlaze ELF UART PASS/FAIL transcript
