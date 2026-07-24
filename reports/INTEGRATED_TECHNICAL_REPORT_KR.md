# 다중 시간 척도 SNN을 적용한 장시간 ECG 4-클래스 저전력 스트리밍 분류 가속기 IP

# I. 설계작품 요약서

ECG는 심장의 전기적 활동을 시간에 따라 기록한 전압 파형이다. 짧은 구간에서는 개별 박동의 모양을 볼 수 있지만, 한 시점의 파형이 장시간 상태를 대표하기 어렵기 때문에 장시간 기록에서는 박동 간격의 반복과 불규칙성, 특정 파형 특징의 지속 시간이 중요하다. 대표적인 ECG 검사인 Holter 검사가 24~48시간 이상 심전도를 기록하는 것도 간헐적으로 나타나는 이상을 포착하기 위해서이다. 본 작품은 장시간 ECG 기록을 공개 데이터베이스 라벨에 따라 네 개의 리듬·질환 관련 범주인 NSR(normal sinus rhythm), CHF-labelled, ARR(arrhythmia-labelled), AF(atrial fibrillation-labelled)로 분류하기 위해 AFE–ADC와 SNN 기반 RTL 분류 가속기 IP를 결합한 통합 구조를 제시하며, 최종적으로 웨어러블 기기에 적용할 수 있는 저전력 반도체 IP 개발을 목표로 한다.

장시간 파형을 처리하는 가장 직접적인 방법은 전체 기록을 저장한 뒤 일괄 분석하는 것이다. 그러나 웨어러블용 반도체 IP에서 전체 파형을 저장하고 반복 처리하는 방식은 메모리와 연산 부담을 증가시킬 수 있다. 이에 본 작품은 분류에 필요한 사건, 리듬 및 파형 증거만 순차적으로 누적하는 SNN 기반 저전력 스트리밍 구조를 채택하였다.

사전 데이터 분석을 통해 네 범주의 구분에 유효한 PNN 기반 박동 간격 규칙성, RDM 기반 박동 간 변동성 및 DSCR 기반 파형 굴곡 등의 핵심 특징을 선정하고, 이를 스파이크 발생과 막전위 기반 증거 누적으로 표현하는 뉴로모픽 구조로 구현하였다. 또한 Holter 판독이 장시간 기록에서 이상 징후가 나타난 구간을 찾아 해석한다는 점에 착안하여, 연속 ECG 입력을 60초 길이의 Window로 나누고 각 구간의 특징을 Snapshot 뉴런층에서 요약하였다. 각 Snapshot의 분류 증거는 특징이 뚜렷할수록 최종 판정 뉴런층에 더 강하게 누적되며, 이를 통해 Window 내부의 단기 변화와 여러 Window에 걸쳐 반복·지속되는 장기 경향을 함께 반영한다. 이러한 계층형 뉴로모픽 구조를 통해 전체 원시 ECG를 저장하지 않고도 장·단기 특징을 지속적으로 갱신하는 다중 시간 척도 저전력 스트리밍 분류 가속기 IP를 구성하였다.

개발은 요구 사항 정의와 데이터 정규화에서 시작하였다. 본래 시스템은 Holter 검사와 같이 24시간 이상 연속 ECG를 처리하는 스트리밍 구조를 목표로 설계하였다. 그러나 NSR, CHF, ARR, AF 분류에 사용한 공개 ECG 데이터베이스는 클래스별 기록 길이가 서로 다르며, 특히 ARR 범주에 사용한 MIT-BIH Arrhythmia Database는 48개의 30분 기록을 제공한다. 이에 모든 클래스에 동일한 조건을 적용하기 위해 평가 입력 길이를 공통으로 확보할 수 있는 30분으로 통일하였다. 따라서 30분은 하드웨어의 처리 한계가 아니라 공개 데이터셋을 공정하게 비교하기 위한 표준 평가 단위이다. 이 평가 기준에 따라 각 원천 ECG record에서 여러 개의 30분 구간을 구성하되, 동일한 record에서 추출된 모든 구간이 학습, 검증, 최종 시험 중 하나에만 포함되도록 분리하였다. 각 30분 구간은 원천 DB label과 가용한 beat/rhythm annotation을 대조하여 해당 클래스의 박동 및 리듬 증거가 충분히 포함되는지 확인하고 라벨 대표성을 점검하였다. annotation은 이 데이터 구성과 품질 점검에만 사용했으며 최종 RTL 입력에는 포함하지 않았다.

데이터 구성과 분할을 마친 뒤, 아날로그부는 MATLAB에서 0.5–150 Hz ECG 대역의 필터, 이득 및 ADC 동적 범위를 설계하고, 이를 ±1.65 V LTspice AFE–S/H–ADC 회로로 구현하여 주파수 응답과 비이상적 조건을 검증하였다. 이때 공개 ECG는 이미 ADC를 거친 디지털 기록이므로, 표본값을 시간축과 전압축에 맞춘 PWL 전압 자극으로 재구성하여 AFE–ADC 검증 입력으로 사용하였다. 이어 동일한 회로 동작을 SystemVerilog XMODEL로 구현하여 1 kSPS signed 12-bit ECG 스트림을 생성하고 디지털 RTL에 전달하였다. 동일한 10초 ECG에 대한 LTspice와 XMODEL의 ADC 출력은 평균 절대 오차 0.6445 LSB와 상관계수 0.999518을 보여 두 모델 간 정합성을 확인하였다.

디지털부는 Python으로 RTL과 동일한 정수 연산을 수행하는 기준 모델을 구축하고, 박동 간격, 리듬 변동, 파형 형태와 질환 관련 사건을 분류 증거로 변환하는 규칙을 설계하였다. 분류 구조의 가중치와 임계값은 학습 및 검증 데이터로 결정하고 RTL로 구현한 뒤 최종 시험 전에 고정하였다. RTL은 표본별 변화량과 강한 사건을 검출하고, 각 60초 구간의 리듬과 파형 증거를 Snapshot 뉴런층에 요약한 뒤 30개의 Snapshot을 Final Membrane에 누적하도록 구현하였다. 설계 고정 후 처음 한 번만 수행한 최종 시험에서는 36개 구간 중 29개를 정확히 분류하여 정확도 80.56%를 기록하였다. Pure RTL 분류 가속기는 9,719 LUT와 5,038 FF를 사용하고 BRAM과 DSP 없이 구현되었으며, 배치 및 배선 후 WNS 8.184 ns를 확보하였다. 1 kSPS 연속 처리 할당전력은 142.0 mW로 추정되었으며, 30분 기록을 36.0129 ms 동안 burst 처리한 뒤 완전히 power-gating하는 이상적 조건에서는 평균 전력이 2.991 µW로 계산되었다.

XMODEL 통합 환경에서 AFE–ADC와 고정 RTL 코어를 직접 연결해 수행한 End-to-End full replay에서는 30분 입력 36개 모두의 최종 클래스와 네 개의 Final Membrane이 독립 RTL/XSim 결과와 일치하였다. 또한 RTL을 AXI 기반 IP로 패키징해 MicroBlaze 시스템에 통합하고 동일한 입력을 FPGA에서 재생한 결과도 XSim 기준과 일치하였다. 결과적으로 본 작품은 ECG 전체를 저장하지 않고 질환 증거를 순차적으로 누적하여 NSR, CHF, ARR, AF를 판정하는 다중 시간 척도 저전력 스트리밍 분류 가속기 IP를 구현하였다.

# II. 설계결과물 설명서

## 1. 설계 개요

### 1.1 설계 요지

ECG 분류에는 개별 박동의 형태뿐 아니라 장시간에 걸친 박동 간격의 불규칙성과 이상 파형의 반복 및 지속성을 함께 분석해야 한다. 그러나 웨어러블 분류 코어에 장시간의 ECG 전체 기록을 저장하고 반복적으로 분석하면 메모리, 연산량, 전력 부담이 증가한다. 본 작품은 이를 해결하기 위해 AFE–ADC와 SNN 기반 스트리밍 RTL 분류 가속기를 결합하여 NSR, CHF, ARR, AF를 판정하는 통합 시스템을 설계하였다.

아날로그부는 HPF, 3-op-amp 계측 증폭기, 60 Hz Active Twin-T 노치 필터, 150 Hz LPF, 버퍼, Sample-and-Hold 및 12-bit ADC로 구성된다. 증폭 및 필터링된 ECG는 1 kSPS signed 12-bit 스트림으로 변환되어 디지털 분류기로 전달된다.

디지털부는 ΔECG와 Strong Event를 이용해 QRS파 후보를 검출한다. QRS파는 심실 수축에 따른 전기적 활동으로, 심장 박동을 식별하는 기준이 되는 급격한 파형 구간이다. 검출된 박동에서 RR 간격(박동 간격), 리듬 불규칙성, 조기·지연 박동과 QRS 형태를 추출해 질환별 증거로 변환한다. 간헐적 이상이 장시간 기록에 묻히지 않도록 ECG를 60초 Window로 나누고, 각 구간의 증거를 Snapshot Membrane에 요약한다. 30개의 Snapshot은 30분 Final Membrane에 누적되어 단기 변화와 장시간 반복성, 지속성을 함께 반영한다. 현재 30분은 공개 데이터베이스의 모든 클래스에서 공통으로 확보할 수 있는 길이에 맞춘 검증 조건이다. 따라서 동일한 스트리밍 구조를 더 긴 Holter ECG 입력으로 확장할 수 있으나, 실제 24시간 길이의 입력은 향후 검증이 필요하다.

디지털 분류기는 일반적인 CNN/RNN 구현처럼 많은 학습 가중치를 별도 메모리에 저장하고 반복적인 곱셈과 누산을 수행하는 대신, SNN 기반 사건 검출과 막전위 누적을 중심으로 구현하였다. 또한 MATLAB–LTspice–XMODEL–Python/Exact C++–RTL/XSim–Vivado–FPGA 재생으로 이어지는 단계별 검증 절차를 구축하였다. 이를 통해 원시 ECG 전체를 저장하지 않고 리듬과 파형 증거만 순차적으로 갱신하는 스트리밍 ECG 분류 가속기 IP를 구현하였으며, 웨어러블 환경에서의 저전력 동작을 지향한다.

### 1.2 창작 과정

![그림 1. 작품 창작 및 통합 과정](../figures/final_submission/창작과정/창작과정%20블록도_가로형.svg)

**그림 1. 작품 창작 및 통합 과정**

2026년 3월에는 장시간 ECG 분석의 메모리, 연산량, 전력 문제를 해결하기 위해 AFE–ADC와 SNN 기반 RTL 분류 가속기 IP를 결합한 시스템을 설계 아이템으로 선정하였다. 이후 아날로그 회로 사전 검증 및 데이터 분석, AFE·ADC 회로 설계, 디지털 가속기 IP 설계로 역할을 분담하고, 파트 간 인터페이스를 1 kSPS signed 12-bit ECG 스트림으로 통일하였다.

2026년 4월부터 6월까지 공개 ECG를 원천 기록 단위로 분리하고 30분 평가 조건을 설정한 뒤, 사전 분석을 통해 클래스 구분에 유효한 박동·리듬·파형 증거를 선정하였다. 이후 아날로그부는 MATLAB, LTspice 및 XMODEL로 필터, 증폭, ADC 동작을 설계·검증하였다. 디지털부는 선정된 증거를 누적하는 SNN 기반 가속기를 RTL로 구현하고, 긴 조합 경로는 파이프라인 분할로 개선하였다.

사전 분석에서는 원천 데이터베이스의 beat 및 rhythm annotation으로 각 30분 구간이 원천 라벨을 뒷받침하는 박동 및 리듬 증거를 충분히 포함하는지 점검하고, RR 간격, PNN 계열 규칙성, 연속 RR 차이, early–late pair, ΔECG 방향 변화, R-peak 진폭, QRS 폭과 말단 활동 후보를 계산하였다. 클래스별 분포, 결측률, 단순 분류율과 하드웨어 구현 가능성을 함께 비교하여 최종 증거 경로를 선정하였다. annotation은 구간의 라벨 대표성 및 데이터 품질 점검과 후보 특징 선정에만 사용했으며, 최종 RTL은 annotation 없이 signed 12-bit ECG에서 사건과 증거를 자체 생성한다. 상세 근거는 [사전 특징 선정 기록](../docs/FEATURE_SELECTION_AND_ANNOTATION_KR.md)과 [`analysis/feature_selection/`](../analysis/feature_selection/)에 보존한다.

2026년 6월부터 7월까지 아날로그·디지털 각 파트의 정합성을 확인한 뒤, 단일 XMODEL 환경에서 AFE–ADC와 고정 Pure RTL 코어를 직접 연결해 36개의 30분 입력의 End-to-End 동작을 검증하였다. AFE–ADC에서 RTL로 전달된 signed 12-bit ECG 스트림은 디지털 검증 입력과 SHA-256 해시값이 36/36 일치했으며, 최종 클래스와 네 개의 Final Membrane도 독립 RTL/XSim 결과와 모든 사례에서 bit-exact하게 일치하였다. 이후 RTL을 AXI IP로 패키징해 MicroBlaze에 통합하고, FPGA 재생 결과가 XSim과 일치함을 확인하였다.

2026년 7월 현재 데이터 분석, 알고리즘 개발, MATLAB, LTspice, XMODEL, Python, Exact C++, RTL 구현과 AXI IP 패키징, MicroBlaze 통합, End-to-End 및 FPGA 검증을 완료하였다. 현재 개발 범위는 모델 기반 AFE–ADC와 FPGA 디지털 IP의 통합 설계 및 검증 단계이며, ASIC 제작과 post-layout 검증은 후속 과제이다.

## 2. 설계기술 설명서

### 2.1 설계 목표

최종 설계 목표는 장시간 ECG를 연속 처리하고, 기록 전반에서 누적한 증거를 종합하여 NSR, CHF, ARR, AF 중 하나의 분류 결과를 출력하는 저전력 스트리밍 가속기 IP를 개발하는 것이다. 시스템은 ECG를 증폭·필터링하고 디지털 코드로 변환하는 AFE–ADC부와, 박동, 리듬, 파형 형태의 증거를 추출해 장시간 누적하는 SNN 기반 RTL 분류기로 구성한다. 전체 원시 파형을 저장하지 않고 표본마다 필요한 상태만 갱신하여 웨어러블 환경에 적합한 메모리 요구량과 연산량을 확보하고자 한다.

AFE는 0.5–150 Hz ECG 대역과 60 Hz 간섭 억제 기능을 갖는 1 kSPS signed 12-bit 스트림 생성을 목표로 한다. 디지털부는 60초 증거를 Snapshot Membrane에 요약하고 30개의 Snapshot을 Final Membrane에 누적하여 30분 기록을 분류한다. 최종 시험 정확도 80% 이상, Pure RTL의 BRAM·DSP 0과 양의 timing slack, FPGA–RTL/XSim 기능 정합을 목표로 하며, 전력은 연속 동작 전력, 판정당 에너지 및 완전 power-gating 가정의 평균 전력으로 구분하여 저전력 구현 가능성을 평가한다.

개발 결과물은 MATLAB과 LTspice의 AFE–ADC 모델, SystemVerilog XMODEL, 합성 가능한 Pure RTL/AXI IP 및 MicroBlaze FPGA 시스템이다. 각 단계는 동일한 신호 규약과 판정 기준으로 연결되며, 향후 스마트워치, ECG 패치, Holter 기록기 등 웨어러블 SoC 적용을 지향한다.

### 2.2 알고리즘 구성 및 결과(예상)

![그림 2. 다중 시간 척도 ECG 분류 알고리즘](../figures/final_submission/알고리즘%20구성%20및%20예상결과/알고리즘%20구조도.svg)

**그림 2. 다중 시간 척도 ECG 분류 알고리즘**

그림 2와 같이 디지털 분류 가속기는 1 kSPS signed 12-bit ECG에서 박동, 리듬, 파형 증거를 추출하고, 이를 60초 Snapshot과 30분 Final Membrane에 누적해 4-클래스를 판정한다. 원시 ECG 전체를 저장하지 않고, 표본이 입력될 때마다 사건을 검출하고 뉴런의 증거 누적값을 순차적으로 갱신하는 스트리밍 구조이다.

현재 표본과 직전 표본의 차이인 ΔECG를 구하고, 그 절댓값이 구간 초기의 입력 변화에 맞춰 자동 설정된 문턱값을 넘으면 부호에 따라 상승 또는 하강 Strong Event를 발생시킨다. 이를 QRS LIF Neuron에 누적해 QRS 후보를 검출하고, 발화 후 상태 초기화와 불응기로 중복 검출을 막는다.

검출된 QRS 박동은 리듬 특징을 추출하는 기준이 된다. RR Counter는 연속된 박동 사이의 표본 수를 세어 RR 간격을 계산한다. PNN은 현재 RR값을 기준으로 다음 RR의 예상 범위를 만들고, 실제 다음 RR이 해당 범위에 포함되는지를 비교하여 연속된 심박 간격의 규칙성을 판정한다. RDM은 현재와 직전 RR의 차이를 계산하여 박동 간 리듬 변동의 크기를 보고, Ectopic Evidence는 짧은 RR 뒤에 긴 RR이 이어지는 early–late 패턴을 부정맥 관련 증거로 반영한다.

파형 형태는 네 개의 병렬 경로에서 분석한다. DSCR은 ΔECG의 방향 전환 횟수를 세어 파형의 굴곡을 나타내고, RAM은 PNN이 예상한 다음 박동 시점 전후에 짧은 관찰창을 열어 진폭의 최댓값을 산출한다. QRS MAF는 박동 전 120표본과 박동 후 100표본에서 Strong Event가 처음 발생한 위치와 마지막으로 발생한 위치의 차이를 이용해 QRS 활동 폭을 계산하고, RBBB-like 경로는 예상 QRS 종료 이후에도 Strong Event가 남는지를 확인해 심실 내 전도 지연성 증거를 생성한다.

각 증거는 클래스별 시냅스 가중치에 따라 60초 Snapshot Membrane에 누적된다. 확정된 Snapshot의 결과는 증거의 강도, 빈도를 반영하여 Final Membrane에 합산되며, 30분 누적이 완료되면 최종 막전위를 비교해 클래스를 출력한다. 이를 통해 원시 ECG 전체를 저장하지 않고도 일부 구간의 강한 이상을 포착하는 동시에, 우발적인 단일 사건보다 여러 구간에서 반복되는 특징을 중요하게 반영할 수 있다.

**표 1. 대표 ECG 제품 및 선행기술과 제안 알고리즘 비교**

| 비교 대상 | ECG 관찰, 처리 방식 | 기존 기술의 최종 결과 | 제안 알고리즘의 차별점 |
|---|---|---|---|
| Apple Watch ECG App | 사용자가 30초 단일유도 ECG 측정 | 측정 시점의 동리듬 또는 심방세동 여부를 중심으로 분류 | 단일 30초 측정이 놓칠 수 있는 간헐적 이상을 장시간 누적해 4개 기록 범주로 판정 |
| Zio Monitor | 최대 14일간 모든 박동을 저장한 뒤 분석 서비스에서 판독 | 부정맥 분석 보고서 | 원시 ECG 저장 부담과 외부 분석 서비스 의존도를 줄일 수 있음 |
| Bauer et al. [3] | ECG 변화 사건을 순환형 SNN으로 분석 | 이상 패턴 유무를 출력 | 단순 이상 검출이 아닌 NSR, CHF, ARR, AF 기록 클래스를 판정 |
| Zihlmann et al. [5] | CNN으로 ECG 구간 특징을 추출, 정보 결합 | Normal, Noise, Other rhythm, AF로 ECG 분류 | 대규모 MAC 연산 없는 SNN 기반 4-클래스 분류 |

표 1은 관찰 범위, 판정 단위, 원시 데이터 저장 방식과 설명 가능성을 기준으로 기존 기술을 비교한 것이다. Apple Watch ECG App은 30초 측정 시점의 리듬을, Zio Monitor는 장기간 저장 후 외부 분석 결과를 제공한다. Bauer 등의 「Real-Time Ultra-Low Power ECG Anomaly Detection Using an Event-Driven Neuromorphic Processor」는 이상 유무를 검출하고 [3], Zihlmann 등의 「Convolutional Recurrent Neural Networks for Electrocardiogram Classification」은 CNN으로 ECG를 네 클래스로 분류한다 [5]. 본 작품은 리듬/파형 증거를 누적하여 간헐적 이상을 포착하고, 30분 ECG 전체를 NSR, CHF, ARR, AF 중 하나로 낮은 하드웨어 복잡도에서 판정한다.

사건 기반 ECG 연구에서 Amirshahi와 Hashemi는 R-peak 주변 개별 beat를 Poisson spike로 변환해 STDP/R-STDP로 분류했고 [1], Chen 등은 level-crossing ADC와 spiking CNN으로 선택된 beat를 N, SVEB, VEB, F로 분류하였다 [2]. 두 연구는 event/SNN ECG hardware의 가능성을 보여주지만 여러 Window의 증거를 장시간 입력의 클래스로 누적하지는 않는다. 장시간 ECG 연구에서는 Shanmugam 등이 약 48시간 기록의 위험 beat sequence를 집계해 patient-level cardiovascular-death risk를 예측했고 [4], DeepHHF는 24시간 Holter를 30초 Window로 나누어 5년 heart-failure risk를 예측하였다 [6]. 검토한 대표 선행연구 범위에서는 NSR, CHF, ARR, AF 분류, Snapshot별 질환 증거의 명시적 상태화, 장시간 증거 누적, RTL/IP/FPGA 구현과 MATLAB–XMODEL–RTL 추적성을 함께 적용한 사례를 확인하지 못하였다. 이는 세계 최초이거나 동일 연구가 없다는 단정은 아니다.

### 2.3 설계회로 구성

본 작품의 회로는 ECG를 증폭 및 필터링하고 디지털 코드로 변환하는 AFE–ADC부, 핵심 증거를 추출 및 막전위에 누적하는 Pure RTL 분류 코어, 그리고 가속기를 제어하고 데이터를 전달하는 MicroBlaze 통합부로 구성된다.

![그림 3. AFE–ADC 신호 흐름 및 비이상성 모델](../figures/final_submission/설계회로%20구성/아날로그%20회로%20구조도.svg)

**그림 3. AFE–ADC 신호 흐름 및 비이상성 모델**

그림 3의 HPF는 약 0.5 Hz 이하의 기저선 변동을 제거하고, 3-op-amp 계측증폭기는 미세한 차동 ECG를 증폭하면서 공통모드 성분을 억제한다. Active Twin-T 노치 필터는 60 Hz 전원선 간섭을 제거하며, 150 Hz LPF와 버퍼는 ECG 대역 밖의 고주파 성분을 제한하고 다음 단의 부하를 분리한다. 이후 Sample-and-Hold와 12-bit ADC가 ±1.65 V 신호를 1 kSPS로 변환하며, ADC 코드는 signed two’s-complement 형식으로 바뀌어 디지털 RTL에 전달된다.

![그림 4. LTspice로 구현한 AFE–S/H–ADC 전체 회로도](../figures/final_submission/설계회로%20구성/full%20schematic%20by%20LTspice.svg)

**그림 4. LTspice로 구현한 AFE–S/H–ADC 전체 회로도**

그림 4는 AFE–ADC 신호 흐름을 RC 소자와 op-amp 모델로 구현한 LTspice 회로이다. 초기 수동 노치 필터의 출력 부하 문제가 있었는데, Active Twin-T 구조와 버퍼를 추가하여 해결하였다.

![그림 5. Vivado RTL Elaborated Design 기반 Pure RTL 분류기의 모듈 계층 구조도](../figures/final_submission/설계회로%20구성/디지털%20RTL%20계층%20구조도_한글호환.svg)

**그림 5. Vivado RTL Elaborated Design 기반 Pure RTL 분류기의 모듈 계층 구조도**

그림 5의 최상위 모듈 snn_ecg_30min_final_top은 signed 12-bit ECG를 u_snapshot에서 처리해 7가지 특징 증거와 클래스 상태를 생성한다. u_final은 30개의 Snapshot을 누적하여 4-클래스의 Final Membrane과 최종 클래스를 출력한다.

![그림 6. Vivado IP Integrator Block Design 기반 IP 통합 구조도](../figures/final_submission/설계회로%20구성/디지털%20IP%20패키징%20통합%20구조도_한글호환.svg)

**그림 6. Vivado IP Integrator Block Design 기반 IP 통합 구조도**

Pure RTL은 AXI IP로 패키징하였다. MicroBlaze는 AXI-Lite를 통한 분류 시작과 결과 확인을, Sample Feeder는 AXI-Stream signed 12-bit 표본 공급을, RTL 가속기는 사건 검출과 증거 누적을 담당한다. 처리가 끝나면 가속기가 done과 IRQ를 발생시키고, MicroBlaze가 최종 결과를 읽어 UART로 출력한다.

**표 2. 대표 ECG 처리 아키텍처와 제안 회로 구성의 구조적 비교**

| 비교 기술 | 일반적인 회로·처리 구성 | 제안 회로 구성 | 핵심 차이 |
|---|---|---|---|
| CPU·MCU 기반 ECG 분석 | 원시 ECG를 메모리에 저장한 뒤 순차 분석 | 표본 입력마다 사건을 검출하고 뉴런 상태를 순차적으로 갱신 | 전체 입력 버퍼 없이 스트리밍 처리 |
| CNN·RNN FPGA 가속기 | 반복적인 MAC 연산과 가중치 메모리 사용 | 비교기, 계수기, 비트 이동, 부호 누산기 사용 | 대규모 MAC 연산 없이 RTL 구현 |
| 분리된 AFE·분류 모델 | AFE·ADC 결과를 저장한 뒤 소프트웨어에서 분류 | 1kSPS signed 12-bit 스트림을 RTL에 직접 전달 | 별도 소프트웨어 분류 없이 RTL에서 클래스 판정 |

표 2와 같이 제안 회로는 AFE–ADC와 RTL 분류기를 공통 스트림으로 직접 연결하고, 원시 ECG 전체를 저장하는 대신 해석 가능한 리듬/파형 증거만 누적하여 적은 하드웨어 자원으로 NSR, CHF, ARR, AF의 최종 클래스를 판정한다.

### 2.4 설계회로 검증

![그림 7. 아날로그 회로 검증 흐름](../figures/final_submission/설계회로%20검증/아날로그%20검증/아날로그%20검증%20흐름.svg)

**그림 7. 아날로그 회로 검증 흐름**

공개 ECG는 이미 ADC를 거친 디지털 기록이므로, 표본값을 시간축과 전압축에 맞춘 PWL 전압 자극으로 재구성하여 시간영역 검증에 사용하였다. MATLAB 기준 모델과 LTspice AC sweep으로 주파수 응답을 비교하고, 동일한 PWL ECG를 LTspice와 XMODEL에 입력하여 1 kSPS signed 12-bit ADC 출력의 정합성을 검증하였다.

![그림 8-1. MATLAB–LTspice 전체 AFE 응답](../figures/final_submission/설계회로%20검증/아날로그%20검증/LTspice%20vs%20Matlab/Overall%20AFE%20Frequency%20Response%20Comparison.svg)

![그림 8-2. 60 Hz Active Twin-T 노치 응답](../figures/final_submission/설계회로%20검증/아날로그%20검증/LTspice%20vs%20Matlab/60%20HZ%20Active%20Twin-T%20Notch%20Response%20Comparison.svg)

**그림 8. MATLAB–LTspice 전체 AFE 응답(좌)과 60 Hz Active Twin-T 노치 응답(우)**

MATLAB과 LTspice의 0.5–150 Hz 대역 및 60 Hz 노치 형상은 유사했으며, 정량 결과는 표 3에 제시하였다.

![그림 9. LTspice–XMODEL ADC 출력 중첩 비교](../figures/final_submission/설계회로%20검증/아날로그%20검증/xmodel%20vs%20LTspice/adc_waveform_full.png)

**그림 9. LTspice–XMODEL ADC 출력 중첩 비교**

그림 9와 같이 동일한 10초 ECG를 LTspice와 XMODEL에 입력하여 10,000개의 signed ADC 코드를 비교하였으며, 정량 결과는 표 3에 제시하였다.

**표 3. AFE·ADC 모델 간 검증 결과**

| 검증 범위 | 핵심 결과 | 의미 |
|---|---|---|
| MATLAB과 LTspice | HPF 0.481174 Hz, IA 이득 200.594 V/V, 60 Hz 감쇠 −83.557 dB, LPF 150.211 Hz, clipping 0건 | MATLAB 공칭 설계가 LTspice 회로 모델에서 재현됨 |
| LTspice와 XMODEL | 평균 오차 +0.0221 LSB, MAE 0.6445 LSB, RMS 1.3020 LSB, 상관계수 0.999518, 지연 0표본 | ECG 파형과 샘플링 시점의 정합 확보 |
| ADC 코드 오차 | ±1 LSB 91.19%, ±5 LSB 98.74%, ±10 LSB 99.89%, 최대 13 LSB | 제한된 오차 범위에서 코드 정합 확보 |

표 3과 같이 MATLAB–LTspice의 AFE 응답과 LTspice–XMODEL의 ADC 코드 정합을 확인하고, XMODEL 출력을 후속 RTL 검증에 사용하였다.

![그림 10. 디지털 회로 검증 흐름](../figures/final_submission/설계회로%20검증/디지털%20검증/디지털%20검증%20흐름.svg)

**그림 10. 디지털 회로 검증 흐름**

디지털 RTL은 Python 등가 모델로 최종 출력을, 독립적인 Exact C++ 모델로 RTL 연산과 내부 상태를 검증하였다. 이어 Full-top XSim에서 표본 수신부터 60초 Snapshot과 30분 최종 판정까지의 제어 흐름을 확인하였다.

**표 4. 디지털 RTL의 단계별 기능 정합 결과**

| 항목 | 정합 결과 |
|---|---|
| Python–RTL | 최종 클래스 36/36, 4-클래스의 Final Membrane 144/144 전부 일치 |
| Exact C++–RTL | RTL 기준 정수 연산 793,595/793,595, 모듈 단위 내부 동작 추적 18/18, 내부 상태 240,000/240,000, Snapshot 경계 1,080/1,080 일치 |
| Full-top RTL | 36/36 시험 사례 통과, 사례별 1,800,000표본 수신, 30 Snapshot, 1회 최종 판정 및 final_valid 정상 발생 |

표 4의 36개 사례에서 RTL 기준 정수 연산, 내부 상태 및 30분 제어 흐름의 불일치가 없었다. 이를 통해 기준 알고리즘이 RTL의 내부 연산과 30분 전체 처리 흐름에 동일하게 반영되었음을 확인하였다.

![그림 11. 아날로그-디지털 통합 검증 흐름](../figures/final_submission/설계회로%20검증/AXI,IP%20및%20mixed%20검증/VAL-03_analog_digital_integration_flow.svg)

**그림 11. 아날로그-디지털 통합 검증 흐름**

AFE–ADC XMODEL과 고정 Pure RTL 코어를 단일 XMODEL 환경에 직접 연결해 36개의 30분 ECG를 중간 파일 없이 처리하였다. AFE–ADC가 RTL에 전달한 signed 12-bit 표본열은 독립 RTL/XSim의 기준 입력과 SHA-256으로 비교하고, 최종 클래스와 네 개의 Final Membrane도 기준 결과와 대조하였다. AXI IP의 제어와 데이터 전송 동작은 XSim에서 별도로 검증하였다.

**표 5. AFE–ADC XMODEL–RTL End-to-End 및 AXI/IP 검증 결과**

| 검증 항목 | 방법 | 결과 |
|---|---|---|
| 입력 데이터 무결성 | AFE–ADC가 RTL에 전달한 signed 12-bit 표본열과 독립 RTL/XSim 기준 입력의 SHA-256 비교 | 36/36 스트림 SHA-256 일치 |
| End-to-End full replay | AFE–ADC와 Pure RTL을 통합한 XMODEL 환경에 36개의 30분 ECG PWL 입력 | 36/36 일치; 각 30분 입력의 전체 표본 처리 후 1회 최종 판정 |
| 최종 출력 기능 정합 | 통합 출력과 독립 RTL/XSim 잠금 기준값 비교 | 최종 클래스 36/36, 네 개의 Final Membrane 144/144 bit-exact |
| AXI/IP 인터페이스 | XSim에서 AXI-Lite 제어/결과 레지스터, AXI-Stream 대기, TLAST, done & IRQ 확인 | 인터페이스 동작 정상, 2/2 testbench PASS |
| MicroBlaze FPGA 통합 | Nexys A7-100T에서 36개 최종 시험 입력 재생 후 UART 출력과 XSim 기준값 비교 | 최종 클래스 36/36, 네 개의 Final Membrane 144/144 bit-exact |

표 5와 같이 단일 XMODEL 환경에서 AFE–ADC와 Pure RTL을 직접 연결한 36개 End-to-End 시험의 입력과 최종 출력이 모두 기준값과 일치하였다. AXI/IP의 제어, 표본 전송, 처리 완료 및 IRQ 동작도 정상적으로 확인되었으며, MicroBlaze 통합 FPGA 재생에서 최종 클래스와 네 개의 Final Membrane이 기준값과 일치하였다.

고정 설계의 재현 절차와 실행 진입점은 [REPRODUCIBILITY_KR.md](../REPRODUCIBILITY_KR.md)에, 각 주장별 근거와 한계는 [claim registry](../project_registry/claim_registry.csv)와 [evidence map](INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv)에 기록하였다.

### 2.5 설계회로 구현 결과

![그림 12. XMODEL AFE–ADC 단계별 시간영역 파형](../figures/final_submission/설계회로%20구현결과/Xmodel%20구현%20결과.svg)

**그림 12. XMODEL AFE–ADC 단계별 시간영역 파형**

그림 12는 재구성한 ECG PWL 전압 자극이 XMODEL AFE–ADC의 필터링, 증폭, 양자화를 거쳐 1 kSPS signed 12-bit 코드로 변환되는 과정을 보여준다. QRS 파형은 유지되었으며 clipping 없이 RTL 입력 스트림이 생성되었다.

![그림 13. Vivado post-route 기반 FPGA 구현 및 계층별 배치 결과](../figures/final_submission/설계회로%20구현결과/FPGA%20구현ㆍ배치%20결과.svg)

**그림 13. Vivado post-route 기반 FPGA 구현 및 계층별 배치 결과**

Pure RTL 분류기를 AXI IP로 패키징하여 MicroBlaze, Sample Feeder, Local Memory, AXI INTC 및 UARTLite와 통합하였다. Pure RTL은 9,719 LUT, 5,038 FF, BRAM 0, DSP 0 및 WNS 8.184 ns로 구현되었다. MicroBlaze 통합 시스템은 12,494 LUT, 8,494 FF, 16 BRAM, 3 DSP 및 WNS 0.097 ns를 확보했으며, 추가된 BRAM과 DSP는 프로세서와 주변장치 자원이다. 기능 정합 결과는 표 5에 제시하였다.

#### RTL timing 병목 분석과 파이프라인 최적화

초기 주요 병목은 `class_score_neurons` 내부의 `rdm_level_spike → pred_class` 조합 경로였다. 이 경로는 약 90 logic levels와 52개의 CARRY4를 포함한 긴 누산, 비교 및 WTA 경로였고, `class_score_neurons`는 주요 자원 및 timing hotspot이었다. 이를 clock 완화가 아니라 다음과 같은 구조적 파이프라인 분할로 해결하였다.

- C24/global readout과 class WTA pipeline 분리
- `segment_done`에서 마지막 사건을 보존하는 `*_next` counter capture와 C24 event/gate/score delta 등록
- RDM·RAM 산술 경로의 exact lookup table 전환
- Snapshot score의 update–adjust–commit 단계와 RBBB gate 평가 시점 정렬
- QRS MAF combinational scan의 timestamp FIFO 기반 다중-cycle 처리
- PNN predictor center 등록과 case lookup 적용
- Final Membrane margin·WTA의 pairwise stage 분리
- ARR scale/commit 경로와 post-segment flush timing 정렬

개선은 **critical path 관측 → pipeline 분할 → timing 재검증 → 기능 등가성 확인** 순서로 수행하였다. 기존 RDM-to-prediction critical path를 제거하고 Python/RTL 및 FPGA 기능 등가성을 유지하면서 timing closure를 달성하였다. 최적화 전 약 17.5k LUT는 historical OOC hotspot 수치이므로 최종 Pure RTL 9,719 LUT와 직접 비교하지 않는다. 설계 이력 commit은 `c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa`와 `5e2e5d0a46be47d8086b8642e055066079bfa4e6`, 고정 최종 RTL은 `c6b80de19cdcad5b7e43fe7835588b629d847f75`이며, 상세 근거는 [RTL timing 최적화 이력](../verification/timing_optimization/RTL_TIMING_OPTIMIZATION_HISTORY_KR.md)에 보존한다.

**표 6. 고정 최종 시험의 NSR·CHF·ARR·AF 혼동 행렬**

| 정답 / 예측 | NSR | CHF | ARR | AF | 합계 |
|---|---:|---:|---:|---:|---:|
| NSR | 9 | 0 | 0 | 0 | 9 |
| CHF | 0 | 6 | 0 | 3 | 9 |
| ARR | 2 | 0 | 7 | 0 | 9 |
| AF | 1 | 0 | 1 | 7 | 9 |
| 합계 | 12 | 6 | 8 | 10 | 36 |

분류 성능은 학습/검증 데이터와 원천 record가 겹치지 않고 모델 선택에도 사용되지 않은 fully held-out 최종 시험 데이터로, 설계 고정 후 최초 한 번만 평가하였다. 36개 30분 ECG 중 29개를 정확히 판정하여 정확도 80.56%, Macro-F1 80.44%, 균형 정확도 80.56%를 기록하였다.

**표 7. 가속기 처리시간 및 전력 분석**

| 항목 | 결과 | 산출 기준 |
|---|---:|---|
| Exact C++ kernel 연산시간 | 1,777.6998 ms | 단일 thread 360회 측정 중앙값 |
| FPGA 가속기 활성시간 | 36.0129 ms | 3,601,290 active cycles @ 100 MHz |
| 코어 처리시간 비율 | 49.36배 | 1,777.6998 ms / 36.0129 ms |
| 1 kSPS 연속 처리 할당전력 | 142.0 mW | 가속기 동적 45.0 mW + FPGA static 97.0 mW |
| 100 MHz burst 할당전력 | 149.5 mW | 가속기 동적 52.5 mW + FPGA static 97.0 mW |
| 판정당 활성 에너지 | 5.3839 mJ | 149.5 mW × 36.0129 ms |
| 이상적 power-gating 평균 전력 | 2.991 µW | 5.3839 mJ / 1,800 s |

가속 성능은 RTL과 동일한 정수 연산과 판정 절차를 C++로 구현한 단일 thread Exact C++ kernel을 기준으로 비교하였다. FPGA의 실제 활성시간은 Exact C++보다 49.36배 짧았다. 1 kSPS 연속 처리 시 할당전력은 142.0 mW로 추정되며, 30분 데이터를 36.0129 ms 동안 burst 처리한 후 전원을 완전히 power-gating하는 이상적 조건에서는 평균 전력이 2.991 µW로 계산된다.

### 2.6 목표 대비 결과 비교

**표 8. 설계 목표 대비 최종 결과**

| 설계목표 | 목표값 | 최종 결과 | 판정 및 보완 방향 |
|---|---|---|---|
| 4-클래스 분류 정확도 | 정확도 80% 이상 | 정확도 80.56%, Macro-F1 80.44% | 달성. 성능 향상을 위해 클래스 데이터 추가 확보 필요 |
| 스트리밍 입력 규격 | 1 kSPS signed 12-bit | 1 kSPS signed 12-bit 직접 인계 구현 | 달성 |
| Pure RTL 메모리, 연산자원 | BRAM 0, DSP 0 | 9,719 LUT, 5,038 FF, BRAM 0, DSP 0 | 달성 |
| Pure RTL FPGA timing | 양의 slack | WNS 8.184 ns | 달성 |
| FPGA 기능 정합 | 클래스, 막전위 전 사례 일치 | 최종 클래스 36/36, 막전위 144/144 bit-exact | 달성 |
| 장시간 ECG 처리 | 24시간 이상 확장 지향 | 30분 검증 | 조건부 달성. 공개 데이터 길이의 제약 극복 필요 |
| 웨어러블 저전력 가능성 | 저전력 분류 IP | FPGA 연속 처리 142.0 mW 추정, power-gating 가정 2.991 µW 산출 | 조건부 달성. ASIC 구현과 power-gating 적용 후 전력 실측 필요 |

본 설계 범위의 모듈 구현과 통합 및 검증을 완료하였으며, 표 8과 같이 분류 성능, 스트리밍 입력, 하드웨어 자원, timing 및 FPGA 기능 정합 목표를 달성하였다. 다만 장시간 처리와 저전력 목표는 각각 30분 입력 검증과 이상적인 power-gating 조건의 산출값에 근거하므로 조건부 달성으로 평가하였다.

본 작품은 웨어러블 기기에 적용 가능한 저전력 반도체 IP를 지향한다. 관련 ECG 전용 ASIC을 조사한 결과, Abubakar 등의 65 nm TNN 기반 프로세서는 13종 비정상 리듬 검출에서 746 nW의 실측 전력을 달성했으며 [7], Zhang 등의 55 nm ANN 기반 프로세서는 개별 심박의 5-클래스 분류에서 12.88 µW를 보고하였다 [8]. 본 작품의 이상적 평균 전력 2.991 µW도 이들과 유사한 저전력 범위에 해당한다. 따라서 웨어러블용 저전력 분류 IP로서의 구조적 가능성을 확인하였다. 또한 선행연구가 주로 개별 심박이나 짧은 이상 리듬을 검출·분류하는 데 비해, 본 작품은 연속 ECG에서 박동·리듬·파형 증거를 장시간 누적하여 기록 전체를 NSR, CHF, ARR, AF 중 하나로 판정한다는 차별점이 있다.

다만 이러한 저전력 가능성과 장시간 분류 구조의 실효성을 최종적으로 입증하려면, ASIC 구현과 power gating 적용, post-layout 분석 및 실리콘 전력 실측이 필요하다. 현재 실제 검증 입력은 30분이며, 24시간 정확도, 처리시간과 전력은 검증하지 않았다. 물리 AFE PCB, ADC silicon, fabricated silicon과 임상 검증도 수행하지 않았다. 또한 공개 데이터베이스별 클래스 결합에 따른 database–class confounding이 남아 있으므로, 동일한 측정 환경에서 수집한 장시간 다중 클래스 ECG로 분류 성능과 실제 24시간 동작을 추가 검증해야 한다. 2.991 µW는 완전 power-gating을 가정한 산출값이지 FPGA 또는 ASIC의 실측 소비전력이 아니다.

### 2.7 국내외 수상 실적

해당 사항 없음

# III. 제품 및 기술요약

## 창의성

본 작품은 분류기 내부에 원시 ECG 전체를 저장하지 않고, 간헐적으로 나타나는 질환 증거를 60초와 30분의 두 시간 척도에서 누적한다. ΔECG와 Strong Event로 QRS파를 검출한 뒤, PNN, RDM 등의 리듬 경로와 DSCR, RAM, QRS MAF, RBBB-like 등의 파형 경로에서 박동 간격, 리듬 변동 및 형태 특징을 해석 가능한 증거로 변환한다. 변환된 증거를 60초마다 Snapshot Membrane에 누적하고, 30분동안 생성된 30개의 Snapshot을 Final Membrane에 누적해 증거의 강도·빈도·지속성을 반영한다. 대규모 MAC 배열과 가중치 메모리 대신 SNN 기반 사건 처리와 막전위 누적 구조를 사용하고, AFE–ADC 모델부터 Pure RTL의 4-클래스 판정까지 직접 연결한 스트리밍 구조가 핵심 창의성이다.

## 기술성

AFE–ADC는 LTspice 회로와 XMODEL로, SNN 분류 가속기는 Pure RTL과 AXI 기반 FPGA IP로 구현하였다. 아날로그부는 목표 ECG 대역과 60 Hz 간섭 억제 특성을 재현해 1 kSPS signed 12-bit 출력을 RTL에 직접 전달하였다. 디지털부는 원시 파형을 저장하지 않고 사건·리듬·파형 증거를 60초와 30분의 두 시간 척도로 누적한다. 설계 고정 후 정확도 80.56%, Macro-F1 80.44%를 기록했으며, Pure RTL은 BRAM·DSP 0과 timing closure를 달성하고 Exact C++보다 49.36배 짧은 활성시간을 보였다. XMODEL–RTL과 MicroBlaze FPGA의 36개 시험도 모두 기준값과 일치하였다. 연속 처리 전력은 142.0 mW로 추정되며, 이상적 power-gating 평균 전력 2.991 µW는 ASIC 저전력화 가능성을 제시한다.

## 사업성

본 IP는 스마트워치, ECG 패치, Holter 기록기와 원격 모니터링 단말의 AFE–ADC 후단에 탑재되는 엣지 분류 블록을 목표로 한다. 장시간 ECG를 저장, 전송한 뒤 외부에서 분석하는 방식은 자원 부담을 높일 수 있다. 제안 IP는 원시 파형 대신 리듬, 파형 증거만 누적하여 기기 내부에서 입력 ECG 전체를 NSR, CHF, ARR, AF 중 하나로 분류한다. BRAM과 DSP를 사용하지 않는 SNN 기반 RTL 구조와 완전 power gating 가정의 평균 전력 2.991 µW는 장시간 착용기기의 저전력 통합 가능성을 보여준다. AXI 기반 독립 IP로 패키징되어 다양한 웨어러블 SoC에 재사용하기도 쉽다. 향후 ASIC 전력 실측과 임상 검증을 거쳐 웨어러블 헬스케어 시장으로 확장할 수 있다.

## 완성도

MATLAB 설계부터 LTspice, XMODEL, 기준 모델, RTL/XSim, Vivado와 FPGA까지 단계별 검증을 완료하였다. 공개 디지털 ECG를 PWL 자극으로 재구성해 아날로그 모델 간 정합을 확인하고, 디지털부는 출력과 내부 상태를 기준 모델과 대조하였다. AFE–ADC와 Pure RTL을 직접 연결한 36개 XMODEL End-to-End 시험에서 입력 SHA-256 36/36, 클래스 36/36, Final Membrane 144/144가 정확히 일치했으며, AXI/IP와 MicroBlaze 통합 FPGA도 정상 동작하였다. 최종 시험은 학습, 검증에 쓰인 record와 겹치지 않고 설계 과정에서 한 번도 사용하지 않은 fully held-out 데이터로, 가중치, 임계값을 고정한 뒤 단 한 번만 수행하였다.

# 참고문헌

1. A. Amirshahi and M. Hashemi, “ECG Classification Algorithm Based on STDP and R-STDP Neural Networks for Real-Time Monitoring on Ultra Low-Power Personal Wearable Devices,” *IEEE Transactions on Biomedical Circuits and Systems*, 2019. https://doi.org/10.1109/TBCAS.2019.2948920
2. J. Chen et al., “An Event-Driven Compressive Neuromorphic System for Cardiac Arrhythmia Detection,” *IEEE International Symposium on Circuits and Systems*, 2022. https://ieeexplore.ieee.org/document/9937756/
3. F. C. Bauer, D. R. Muir, and G. Indiveri, “Real-Time Ultra-Low Power ECG Anomaly Detection Using an Event-Driven Neuromorphic Processor,” *IEEE Transactions on Biomedical Circuits and Systems*, 2019. https://doi.org/10.1109/TBCAS.2019.2953001
4. D. Shanmugam, D. Blalock, and J. Guttag, “Multiple Instance Learning for ECG Risk Stratification,” *Proceedings of Machine Learning for Healthcare*, 2019. https://proceedings.mlr.press/v106/shanmugam19a.html
5. M. Zihlmann, D. Perekrestenko, and M. Tschannen, “Convolutional Recurrent Neural Networks for Electrocardiogram Classification,” *Computing in Cardiology*, 2017. https://doi.org/10.22489/CinC.2017.070-060
6. E. Zvuloni et al., “Modeling day-long ECG signals to predict heart failure risk with explainable AI,” *npj Digital Medicine*, 2026. https://doi.org/10.1038/s41746-026-02835-8
7. A. Abubakar et al., “A 746 nW ECG Processor ASIC Based on Ternary Neural Network,” *IEEE Transactions on Biomedical Circuits and Systems*, 2022. https://doi.org/10.1109/TBCAS.2022.3196059
8. C. Zhang et al., “A Low-Power ECG Processor ASIC Based on an Artificial Neural Network for Arrhythmia Detection,” *Applied Sciences*, 2023. https://doi.org/10.3390/app13179591
