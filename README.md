# 다중 시간 척도 SNN을 적용한 장시간 ECG 4-클래스 저전력 스트리밍 분류 가속기 IP

이 저장소는 AFE–ADC와 SNN 기반 RTL 분류 가속기 IP를 결합하여 장시간 ECG 기록을 **NSR, CHF, ARR, AF** 중 하나로 분류하는 통합 구조의 설계, 모델, RTL, Vivado project와 검증 근거를 한곳에 보존한다.

제출 보고서의 문장과 표현을 그대로 옮긴 기준 본문은 [통합 기술보고서](reports/INTEGRATED_TECHNICAL_REPORT_KR.md)다. 보고서 분량 때문에 싣지 못한 사전 특징 분석, timing 병목 개선과 재현 근거는 기준 본문과 구분하여 별도 기술기록으로 보존한다.

> 현재 검증 입력은 공개 데이터베이스 조건에 맞춘 **30분**이다. 24시간 이상 Holter ECG는 설계 지향점이며, 실제 24시간 정확도, 처리시간과 전력은 아직 검증하지 않았다.

## 핵심 아이디어

사전 데이터 분석을 통해 네 범주의 구분에 유효한 PNN 기반 박동 간격 규칙성, RDM 기반 박동 간 변동성 및 DSCR 기반 파형 굴곡 등의 핵심 특징을 선정하고, 이를 스파이크 발생과 막전위 기반 증거 누적으로 표현하는 뉴로모픽 구조로 구현하였다. 연속 ECG 입력을 60초 길이의 Window로 나누고 각 구간의 특징을 Snapshot 뉴런층에서 요약하며, 여러 Window에 걸쳐 반복·지속되는 장기 경향을 최종 판정에 함께 반영한다.

이러한 계층형 뉴로모픽 구조를 통해 전체 원시 ECG를 저장하지 않고도 장·단기 특징을 지속적으로 갱신하는 다중 시간 척도 저전력 스트리밍 분류 가속기 IP를 구성하였다.

![다중 시간 척도 ECG 분류 구조](figures/final_submission/알고리즘%20구성%20및%20예상결과/알고리즘%20구조도.svg)

## 구현 범위

```text
공개 digitized ECG
  → PWL 전압 자극 재구성
  → MATLAB 공칭 설계
  → LTspice AFE, S/H, ADC
  → SystemVerilog XMODEL
  → 1 kSPS signed 12-bit stream
  → SNN Pure RTL
  → AXI IP, MicroBlaze
  → Vivado implementation, Nexys A7-100T replay
```

- 아날로그 모델: HPF, 3-op-amp IA, Active Twin-T 60 Hz notch, 150 Hz LPF, buffer, S/H, 12-bit ADC
- 디지털 코어: Strong Event, QRS LIF, PNN, RDM, Ectopic Evidence, DSCR, RAM, QRS MAF, RBBB-like, Snapshot/Final Membrane
- 인터페이스: AXI-Lite control/result, AXI-Stream signed 12-bit input, done/IRQ, UART result
- Vivado project: Pure RTL hierarchy용 1개, MicroBlaze 구현·replay용 1개

## 최종 결과

| 항목 | 결과 | 주장 범위 |
|---|---:|---|
| 잠금 최종 시험 | 29/36, 정확도 80.56%, Macro-F1 80.44% | 30분 public-dataset engineering result |
| 원천 record별 집계 | 16/19, 정확도 84.21% | 같은 final partition의 집계이며 별도 시험이 아님 |
| Pure RTL 구현 | 9,719 LUT, 5,038 FF, BRAM 0, DSP 0 | Artix-7 XC7A100T, Vivado 2020.2 |
| Pure RTL timing | WNS 8.184 ns | post-route timing closure |
| MicroBlaze 통합 | 12,494 LUT, 8,494 FF, 16 BRAM, 3 DSP, WNS 0.097 ns | 전체 시스템 자원 |
| FPGA 기능 정합 | class 36/36, Final Membrane 144/144 | XSim 대비 기능 등가성, 분류 정확도와 다름 |
| Exact C++ 대비 활성시간 | 1,777.6998 ms 대 36.0129 ms, 49.36배 | 단일 thread kernel 대 profiler counter 기반 FPGA core |
| 1 kSPS 연속 할당전력 | 142.0 mW | post-route activity 기반 추정, 보드 실측 아님 |
| 이상적 평균전력 | 2.991 µW | 30분마다 36.0129 ms 동작 후 완전 power-gating을 가정한 산출값 |

LTspice와 XMODEL의 동일 10초 ECG 비교에서는 MAE 0.6445 LSB, RMS 1.3020 LSB, 상관계수 0.999518, 지연 0표본을 기록했다. 이는 모델 간 정합이며 물리 AFE 또는 ADC 실측이 아니다.

## 평가 원칙

- 한 원천 ECG record에서 파생한 모든 30분 구간은 train, validation, final test 중 하나에만 속한다.
- 구조, 가중치와 임계값은 train/validation으로 결정한 뒤 고정했다.
- final test는 모델 선택에 사용하지 않았으며 설계 고정 후 한 번만 평가했다.
- 클래스는 서로 다른 공개 DB와 결합되어 있으므로 database–class confounding이 남는다.
- 공개 문서에서는 `AF`를 사용한다. 고정 model ID, RTL port와 과거 파일명의 `AFF`는 재현성을 위해 변경하지 않는다.

자세한 내용은 [통합 기술보고서](reports/INTEGRATED_TECHNICAL_REPORT_KR.md), [claim registry](project_registry/claim_registry.csv), [evidence map](reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv)에서 확인할 수 있다.

## 저장소 안내

| 목적 | 경로 |
|---|---|
| 빠른 파일 찾기 | [START_HERE_KR.md](START_HERE_KR.md) |
| 데이터와 평가 | [docs/DATASET_AND_EVALUATION_KR.md](docs/DATASET_AND_EVALUATION_KR.md) |
| 사전 분석과 annotation | [docs/FEATURE_SELECTION_AND_ANNOTATION_KR.md](docs/FEATURE_SELECTION_AND_ANNOTATION_KR.md) |
| SNN/RTL 구조 | [docs/DIGITAL_ARCHITECTURE_KR.md](docs/DIGITAL_ARCHITECTURE_KR.md) |
| timing 병목 개선 | [verification/timing_optimization/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md](verification/timing_optimization/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md) |
| 하드웨어와 전력 | [docs/HARDWARE_IMPLEMENTATION_KR.md](docs/HARDWARE_IMPLEMENTATION_KR.md) |
| 통합 검증 | [docs/INTEGRATION_VERIFICATION_KR.md](docs/INTEGRATION_VERIFICATION_KR.md) |
| 최종 Figure | [figures/FIGURE_INDEX.md](figures/FIGURE_INDEX.md) |
| 재현 명령 | [REPRODUCIBILITY_KR.md](REPRODUCIBILITY_KR.md) |

## 중요한 검증 범위 구분

`verification/xmodel_rtl_acceptance_36case/`는 과거 고정 AFE 생성 36개 chunk와 digital replay 입력의 SHA-256 동일성, canonical cadence에서 class 36/36 및 membrane 144/144를 기록한 **compact acceptance evidence**다.

`verification/xmodel_rtl_e2e/`는 실제 full-30분 raw XMODEL accepted dump를 저장소 단독으로 다시 replay한 감사 자료다. 현재 raw dump는 4개만 보존되어 4개는 bit-exact PASS이고 나머지 32개는 재생성 환경이 필요하다. 두 근거의 범위를 혼합하지 않는다.

## 한계

물리 AFE PCB, ADC silicon, ASIC post-layout, fabricated silicon, 임상 검증과 실제 24시간 입력 검증은 수행하지 않았다. FPGA 전력은 추정치이고 2.991 µW는 이상적 power-gating 가정값이다. 본 결과는 임상 진단이나 상용 의료기기 대비 우월성을 뜻하지 않는다.
