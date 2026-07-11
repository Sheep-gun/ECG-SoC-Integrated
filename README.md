# ECG-SoC Integrated Technical Repository

## 1. 프로젝트 정체성

본 프로젝트는 Holter형 장시간 ECG 분석을 위해 60초 Snapshot과 30분 Final Membrane을 결합한 다중 시간축 SNN-inspired 분류 구조를 제안하고, 이를 signed 12-bit streaming RTL accelerator IP로 구현·검증한 연구이다.

## 2. 연구 배경

Wearable·portable ECG는 일상에서 single-lead waveform과 rhythm screening 정보를 제공할 수 있다. 대표 소비자 기능은 AF/sinus 중심의 제한된 scope를 갖지만, 본 연구 문제는 공개 digitized ECG의 장시간 stream에서 local morphology와 long-term persistence를 함께 다루는 투명한 hardware architecture다. 제품별 clinical 성능과 본 project의 public-dataset accuracy는 조건이 달라 직접 비교하지 않는다.

장시간 ambulatory ECG는 local beat evidence와 장기 반복·지속성을 함께 관찰해야 한다. 본 설계는 이 두 시간축을 Snapshot과 Final Membrane으로 명시적으로 분리한다. 배경 출처와 해석 경계는 [`RESEARCH_BACKGROUND_KR.md`](docs/RESEARCH_BACKGROUND_KR.md) 및 [`external_reference_registry.csv`](source_of_truth/external_reference_registry.csv)에 있다.

## 3. 문제 정의

입력은 1 kSPS signed 12-bit two's-complement ECG stream이고 출력은 NSR, CHF, ARR, AFF 네 public-dataset class 가운데 하나다. 네 class는 서로 다른 PhysioNet DB에서 온 engineering labels이며 네 질환의 확진을 뜻하지 않는다. 목표는 전체 30분 raw waveform을 buffer한 뒤 batch 처리하지 않고, sample-by-sample state update로 30분 decision을 만드는 것이다.

## 4. 제안 다중 시간축 구조

Signed sample에서 beat timing, RR variability, slope/morphology, R-peak amplitude, ectopic-like pair와 QRS-related evidence를 integer event/state로 갱신한다. 60,000 samples마다 Snapshot Readout이 local class evidence를 만들고, 30개 Snapshot의 signed evidence가 Final Membrane에 누적된다. 마지막 WTA가 30분 window의 class를 선택한다.

![60-second Snapshot and 30-minute Final Membrane](figures/final/FIG-04_multitimescale_architecture.svg)

`SNN-inspired`는 event와 membrane-like persistent state를 사용한다는 뜻이다. Trained deep SNN, biological equivalence 또는 online learning을 주장하지 않는다.

## 5. 전체 시스템 흐름

`public ECG → MATLAB nominal AFE+ADC pre-validation → SystemVerilog AFE+ADC XMODEL verification → signed 12-bit stream → Snapshot/Final Membrane → RTL/XSim → Vivado/IP-XACT → Vitis/MicroBlaze → FPGA replay`

![Complete system flow](figures/final/FIG-02_complete_system_flow.svg)

MATLAB은 nominal intent와 reference vector, XMODEL은 model-based non-ideal/stress와 long-stream handoff, digital component는 locked classifier/RTL/IP/FPGA를 담당한다.

## 6. 핵심 기술 기여

1. Binary AF/sinus보다 넓은 네 public-dataset class의 long-window engineering target
2. 60초 Snapshot과 30분 Final Membrane의 multi-timescale temporal hierarchy
3. Integer counter·comparator·signed accumulator 기반 event/state streaming realization
4. MATLAB–XMODEL–digital 사이의 signed-stream SHA256 및 canonical output reproduction
5. Python reference–RTL/XSim–Vivado–IP-XACT–Vitis–FPGA로 이어지는 implementation chain
6. Fixed commits, per-file SHA256, ownership, metric와 claim registry를 갖춘 evidence control

Hardware efficiency와 accelerator performance는 이 구조를 지원하는 evidence이며 primary novelty가 아니다.

## 7. 검증된 분류 결과

| Result | Value | Interpretation |
|---|---:|---|
| Train | 61/68 = 89.71% | fitting evidence |
| Validation | 32/32 = 100.00% | model selection only |
| Locked final-test 30-minute chunk | 29/36 = 80.56% | primary held-out engineering result |
| Chunk macro F1 | 80.44% | final-test |
| Final-test record-majority | 16/19 = 84.21% | same final partition aggregated by record |
| Record-majority macro F1 | 80.80% | aggregation result |

Final test는 model selection에 쓰지 않았고 lock 이후 evaluation count는 1이다. Validation 100%는 final generalization claim이 아니다.

![Locked classification result](figures/final/FIG-10_classification_summary.svg)

## 8. Mixed-signal-to-digital 검증

- MATLAB representative NSR/CHF/ARR/AFF nominal records: clipping 0%; minimum rail headroom 약 1.0196 V
- Emulator ↔ Questa/XMODEL 36 segments: mean RMS 1.95 LSB, lag 0
- AFE-generated final-test chunks ↔ digital board inputs: SHA256 36/36
- Canonical `sample_gap_cycles=2`: AFE-to-locked RTL final_pred 36/36, final_mem 36/36 bit-exact

이 결과는 model-based signal-chain과 digital handoff evidence다. Physical AFE PCB, ADC silicon, transistor/post-layout 또는 live-electrode validation이 아니다.

## 9. RTL/IP/FPGA 구현

| Profile | LUT | FF/register | BRAM | DSP | Timing evidence |
|---|---:|---:|---:|---:|---:|
| Pure RTL | 9719 | 5038 | 0 | 0 | WNS 8.184 ns |
| MicroBlaze full-replay system | 12494 | 8494 | 16 | 3 | setup WNS 0.097 ns |

Pure RTL과 full MicroBlaze system은 resource scope가 다르다. Board replay는 final_pred와 final_mem이 각각 36/36 expected output과 일치했다. Label 기준 classification accuracy는 29/36이며 36/36이 아니다.

## 10. 저장소 구조

```text
components/             three commit-pinned upstream snapshots
source_of_truth/        commits, hashes, metrics, claims, owners, terms, references
docs/                   research positioning and technical integration narratives
integration_evidence/   upstream before/after status and intentional exclusions
figures/source/         verified figure source data
figures/final/          11 generated non-benchmark SVG figures
tables/                 classification, implementation, integration tables
benchmarks/             pending external benchmark placeholder only
reports/                integrated integrity-check report
tools/                  import, metric, figure, and integrity tools
private_submission/     Git-blocked private-report area
```

## 11. Contributor ownership

| Contributor | Ownership |
|---|---|
| 서민우 | MATLAB nominal AFE+ADC, parameter/gain/frequency reference, ADC headroom/clipping, signed vectors/manifests |
| 이수환 | SystemVerilog XMODEL, non-ideal/stress, full-record AFE output, AFE-to-digital integration evidence |
| 양건 | project lead, multi-timescale architecture, strict evaluation/locked model, RTL/XSim/Vivado/IP-XACT/Vitis/board, final integration |

Machine-readable canonical record는 [`ownership_matrix.csv`](source_of_truth/ownership_matrix.csv)다.

## 12. 한계와 claim 경계

- 본 prototype은 clinically validated diagnostic device가 아니다.
- AFE/ADC chain은 MATLAB/XMODEL 기반이며 fabricated silicon이 아니다.
- NSR/CHF/ARR/AFF가 서로 다른 DB에서 와 database-class confounding이 남는다.
- Strict record-wise split은 direct record leakage를 막지만 confounding을 해결하지 않는다.
- Board 36/36은 functional equivalence이고 classification accuracy는 29/36이다.
- Commercial product와 clinical sensitivity/specificity를 직접 비교하지 않는다.

자세한 wording control은 [`claim_registry.csv`](source_of_truth/claim_registry.csv)와 [`LIMITATIONS_AND_CLAIM_BOUNDARY_KR.md`](docs/LIMITATIONS_AND_CLAIM_BOUNDARY_KR.md)를 따른다.

## 13. 재현성과 무결성

세 component는 working tree가 아니라 fixed Git objects에서 export됐다. `artifact_manifest.csv`는 imported 1,890개 파일의 origin, fixed commit, upstream/integrated path, size와 SHA256을 기록한다. 다음 명령은 metric과 figure를 다시 만들고 repository claim/integrity를 검사한다.

```powershell
python tools/build_global_metrics.py
python tools/generate_integrated_figures.py
python tools/check_integrated_repository.py
```

Application forms와 Office lock file 네 개는 정책상 제외됐고 hash가 `integration_evidence/excluded_upstream_paths.csv`에 남아 있다. 최종 private HWP/PDF와 개인정보는 이 Git 밖에 둔다.

## 14. Accelerator benchmark 상태

Status: `PENDING_EXTERNAL_BENCHMARK_IMPORT`

Latency, throughput, speedup, power와 energy benchmark는 별도 작업에서 진행 중이다. 현재 integrated benchmark fields는 모두 `null`이며 zero가 아니다. 외부 package의 commit, input hash, measurement scope, raw/result CSV와 measured/cycle-derived/estimated 구분을 검증한 뒤에만 가져온다.
