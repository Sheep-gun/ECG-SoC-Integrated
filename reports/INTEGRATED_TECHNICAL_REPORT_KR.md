# 장시간 ECG 4-Class 분류를 위한 다중 시간축 SNN-Inspired Streaming RTL Accelerator IP

# 초록

장시간 심전도(electrocardiogram, ECG) 분석에서는 한 박동의 모양뿐 아니라 박동 간격과 파형 특징이 수십 분 동안 어떻게 반복되는지도 함께 보아야 한다. 본 연구는 공개 ECG에서 NSR·CHF·ARR·AFF 네 클래스를 자동 분류하기 위해 장시간 입력을 제한 길이 Snapshot으로 순차 처리하고, 간헐적으로 강하게 나타나는 질환 증거의 강도·빈도·반복성과 장시간 일관성을 기록 단위 상태로 누적하는 구조를 제안하였다. 먼저 MATLAB에서 HPF, 3-op-amp IA, 60 Hz notch, LPF와 12-bit ADC의 공칭 응답·동적 범위·기준 벡터를 검증하였다. 이어서 SystemVerilog XMODEL로 AFE·ADC 회로망을 구성하고 전원선 간섭, R/C mismatch, 유한 GBW와 입력 offset, ADC 비이상성 및 장시간 signed stream을 검토하였다. 이 스트림을 받는 디지털 IP는 인접 표본값의 차이에서 사건을 만들고, 반복되는 강한 변화를 막전위형 상태에 누적해 박동을 검출한다. RR 간격의 규칙성과 변동성, 기울기 방향 전환, 최대 진폭, QRS 주변의 폭·복잡도·에너지를 고정 폭 정수 상태로 압축한다. 현재 공개 데이터 검증에서는 60초 증거 30개를 Final Membrane에 누적해 최종 클래스를 선택한다. 구현은 Python 정수 기준 모델, RTL/XSim, Vivado, AXI/IP-XACT, Vitis/MicroBlaze와 FPGA 재생으로 이어지며, AFE 출력에서 보드 입력까지 SHA256과 내부 상태를 비교하였다. 원천 record 단위로 분리한 고정 최종 시험의 30분 구간 정확도는 29/36=80.56%, record-majority 정확도는 16/19=84.21%였다. Pure RTL은 LUT 9,719, FF 5,038, BRAM 0, DSP 0으로 구현되었고 FPGA의 `final_pred`와 `final_mem`은 XSim 기준과 각각 36/36 일치하였다. 저장된 30분 ECG 처리에서는 단일 스레드 Exact C++ 1,777.699800 ms와 cycle-derived FPGA core 54.012600 ms를 비교해 32.912687배의 처리시간 비율을 얻었다. 이는 물리 보드에서 측정한 speedup이 아니며 live 판정은 여전히 30분 관찰을 필요로 한다. 클래스와 데이터베이스의 결합, 실제 AFE/ADC·임상 검증 부재와 물리 보드 timing·전력 미측정이 남아 있으므로, 본 결과는 임상 진단 성능이 아니라 MATLAB→AFE·ADC XMODEL→디지털 가속기 IP→FPGA로 이어지는 장시간 ECG 분류 시스템의 공학적 구현과 검증으로 한정한다.

본 연구의 핵심은 60초와 30분이라는 숫자 자체가 아니다. 장시간 Holter ECG를 제한된 길이의 Snapshot으로 순차 처리하고, 대부분 정상으로 보이는 기록 속에서 간헐적으로 나타나는 질환성이 강한 Snapshot을 포착한 뒤, 질환 증거의 강도·출현 빈도·반복성과 장시간 일관성을 설명 가능한 상태로 누적하여 전체 기록의 클래스를 판정하는 streaming architecture다 [CLM-042].

본 연구의 출발점은 24시간 Holter형 관찰이지만, 네 클래스에 사용한 공개 데이터베이스의 record 길이가 서로 다르고 MIT-BIH Arrhythmia Database가 30분 excerpt로 제공되므로 현재 통합 평가 창은 30분으로 고정하였다. 따라서 30분 결과는 동일 길이의 공개 데이터로 검증한 prototype 범위이며, 임상적 24시간 Holter와 동등하다는 뜻은 아니다 [CLM-035].

# 핵심어

심전도, 장시간 모니터링, SNN-inspired 구조, 사건 기반 처리, Snapshot 판독, Final Membrane, streaming RTL, FPGA 가속기

# 1. 서론

## 1.1 연구 배경과 문제 정의

ECG는 심장의 전기적 활동을 시간에 따라 기록한 전압 파형이다. 짧은 구간에서는 개별 박동의 모양을 자세히 볼 수 있지만, 장시간 기록에서는 박동 간격의 반복과 불규칙성, 특정 파형 특징이 얼마나 오래 지속되는지가 함께 중요하다. Ambulatory ECG가 증상 빈도와 관찰 목적에 따라 24/48시간 Holter 또는 더 긴 감시 방식을 사용하는 이유도 한 시점의 파형만으로 장시간 상태를 대표하기 어렵기 때문이다[2].

원래 설계 목표는 이러한 24시간 Holter 관찰 흐름을 사건·상태형 반도체 IP로 처리하는 것이었다. 그러나 이번 네 클래스는 길이가 같은 단일 cohort가 아니라 서로 다른 공개 데이터베이스에서 왔다. 특히 ARR에 사용한 MIT-BIH Arrhythmia Database는 24시간 ambulatory 원본 집합에서 선택한 48개의 **30분 excerpt**로 구성된다[11]. 한 클래스에만 없는 시간을 반복하거나 0으로 채우지 않고 모든 클래스에 동일한 실제 관찰 길이를 적용하기 위해 30분을 현재 공통 비교 단위로 선택하였다 [CLM-035]. 따라서 `Holter-oriented`는 24시간 장기 관찰을 지향하는 구조적 동기이고, 현재 결과는 30분 prototype 검증이다. 30분 결과가 임상적 24시간 Holter를 대체하거나 동등하다는 뜻은 아니다.

대표적인 소비자용 단일유도 ECG 앱의 FDA 문서 사례는 정상 동율동과 심방세동 중심의 리듬 선별 범위를 설명한다[1]. 본 연구는 그 제품과 정확도를 비교하지 않는다. 공개 데이터에서 NSR(normal sinus rhythm), CHF-labelled, ARR(arrhythmia-labelled), AFF(atrial-fibrillation-labelled) 네 범주를 다루는 장시간 공학 문제를 정의하고, 국소 리듬·파형 증거를 30분 동안 누적하는 투명한 하드웨어 구조를 설계한다. NSR은 질병이 아니며 ARR은 넓은 표지이고 CHF 역시 해당 원천 데이터베이스의 표지다. 따라서 출력은 네 질환의 확진이 아니라 현재 공개 데이터 구성에서 정의한 네 클래스다 [CLM-001].

장시간 파형을 다루는 가장 직접적인 방법은 전체 기록을 저장한 뒤 소프트웨어에서 일괄 분석하는 것이다. 그러나 wearable용 반도체 IP를 목표로 할 경우에는 입력이 들어오는 동안 필요한 정보만 작은 상태로 남기는 구조가 더 적합하다. 이때 해결해야 할 문제는 단순히 계산을 빠르게 만드는 것이 아니다. 1 ms마다 들어오는 표본값의 변화, 수백 ms 규모의 박동, 60초 구간의 리듬과 30분 동안 반복되는 특징을 하나의 회로에서 잃지 않고 연결해야 한다.

이를 위해 다음 세 시간척도를 동시에 유지한다.

- **표본값 시간척도:** 1 ms마다 파형 변화와 검출기 상태를 갱신한다.
- **박동 시간척도:** 검출된 박동 사이 간격과 박동 중심 파형 구간을 평가한다.
- **구간·장시간 시간척도:** 60초 증거를 Snapshot으로 확정하고 30개 Snapshot을 Final Membrane에 누적한다.

![그림 1. 장시간 ECG에서 서로 다른 시간척도의 증거](../figures/final/FIG-01_long_window_motivation.svg)

*그림 1. 표본값·박동·제한 길이 Snapshot·장시간 기록 상태로 이어지는 문제의 시간 계층. 그림의 60초·30분은 현재 공개 데이터 검증 설정이며 architecture의 고정된 본질이나 임상 인증을 뜻하지 않는다. [근거: CLM-001, CLM-003, CLM-035, CLM-042]*

## 1.2 연구 목표와 주요 기여

연구 목표는 공개 ECG를 공통 signed 12-bit 스트림으로 변환하고, 장시간 기록을 순차 Snapshot으로 처리하면서 간헐적으로 강하게 나타나는 리듬·파형 형태·질환별 증거를 보존하여 기록 단위 클래스를 출력하는 RTL IP를 만드는 것이다. 속도 자체나 60초·30분이라는 특정 길이가 주 기여는 아니다. 핵심은 Snapshot별 증거의 강도, 출현 빈도, 반복성과 장시간 일관성을 설명 가능한 고정 폭 상태로 구현하고, 모델로 정의한 아날로그 의도부터 FPGA 출력까지 같은 신호와 상태를 추적하는 데 있다 [CLM-042].

주요 기여는 다음 여섯 가지다.

1. NSR·CHF·ARR·AFF를 대상으로 하는 장시간 4-Class 공학 목표를 정의하였다.
2. 대부분 정상인 장시간 기록에서 질환성이 강한 Snapshot을 포착하고, 국소 증거의 강도·빈도·반복성과 장시간 일관성을 기록 단위 상태로 재결합하였다.
3. 인접 표본값 변화, 막전위형 박동 검출, RR 리듬과 파형 형태를 정수 계수기·비교기·누산기로 구현하였다.
4. 전체 장시간 원시 관찰 구간을 저장하지 않고 고정 크기 지속 상태를 갱신하는 streaming datapath를 구현하였다. 현재 검증 입력은 30분이다 [CLM-023, CLM-035].
5. MATLAB→XMODEL→부호 있는 스트림→RTL/IP→FPGA로 이어지는 기능 등가성 사슬을 구축하였다.
6. 고정 commit, 산출물 hash, 데이터셋 manifest, 담당자·claim registry와 checker로 수치와 해석 경계를 통제하였다.

이후 제2장에서는 기존 접근의 한계에서 설계 요구를 도출하고 전체 시스템과 평가 방법을 설명한다. 제3장은 MATLAB에서 공칭 AFE·ADC 응답과 기준 벡터를 먼저 고정한다. 제4장은 이 설계값을 회로망으로 옮긴 AFE·ADC XMODEL과 비이상성 검증을 다룬다. 제5장은 signed stream을 받아 네 클래스를 판정하는 디지털 가속기 IP와 FPGA 구현을 설명한다. 제6장은 가속기 benchmark의 반영 범위와 AFE·디지털 통합 검증을 분리해 제시한다. 제7장에서 결과를 모아 비교하고, 제8장에서 의미와 한계를 논의한 뒤 제9장에서 결론을 정리한다.

| 목표 | 구현·검증 결과 | 해석 경계 |
|---|---|---|
| 장시간 네 클래스 분류 | 60초 Snapshot×30, 최종 29/36 | 공개 데이터셋 기반 공학 결과 |
| 사건/상태형 RTL | 고정 폭 계수기·비교·부호 막전위 | 학습된 심층 SNN 아님 |
| 전체 관찰 구간 비저장 | 표본별 지속 상태 갱신 | 측정된 메모리 절감량 아님 |
| Mixed-signal 인계 | SHA256와 canonical pred/mem 36/36 | 모델 기반 아날로그 |
| FPGA IP | Vivado·IP-XACT·MicroBlaze·보드 재생 | 임상 장치/ASIC 아님 |
| 가속기 효과 | Exact C++ 1,777.699800 ms 대 cycle-derived core 54.012600 ms | 32.912687배 추정; board 측정 아님 |

*표 1. 연구 목표와 달성 결과. 각 행은 서로 다른 증거 범위를 갖는다. [근거: CLM-003, CLM-004, CLM-008~CLM-013, CLM-018, CLM-023]*

표 1의 가속기 benchmark는 저장 데이터의 CPU kernel과 FPGA accelerator-core 처리범위를 맞춘 보조 구현 결과다. 분류 구조가 주 기여이며, 32.912687배는 measured CPU와 cycle-derived core를 결합한 추정이므로 물리 보드 전체의 고속·저전력 우월성으로 확대하지 않는다 [CLM-043~CLM-046].

# 2. 관련 기술과 시스템 설계

## 2.1 장시간 ECG 분석과 사건 기반 분류 선행연구

장시간 ECG에서는 이상 소견이 기록 전체에 계속 나타나지 않을 수 있다. 대부분 정상처럼 보이다가 특정 시간대나 몇 번의 박동에서만 강한 질환 특징이 나타날 수 있다. 따라서 선행연구를 비교할 때는 세부 회로나 신경망 종류보다 **“ECG를 어느 범위까지 보고, 마지막에 어떤 질문에 답하는가”**를 먼저 구분해야 한다. 개별 심박의 종류를 맞히는 연구, 연속 ECG에서 이상 구간을 알리는 연구, 긴 기록을 모아 환자의 위험도를 예측하는 연구는 모두 ECG를 다루지만 최종 목적이 서로 다르다.

본 연구가 답하려는 질문은 **“장시간 기록의 일부 구간에서 나타난 질환 증거를 모았을 때, 이 기록 전체는 NSR·CHF·ARR·AFF 가운데 어느 클래스인가?”**이다. 연속 ECG를 제한된 길이의 Snapshot으로 차례로 나누고, 각 Snapshot에서 질환성이 강한 구간을 포착한다. 이후 그 증거가 얼마나 강했는지, 몇 번 나타났는지, 반복되거나 오래 유지됐는지를 누적해 기록 전체의 클래스를 정한다. 현재 60초 Snapshot 30개와 30분 입력은 공개 데이터 길이에 맞춘 검증 조건이며, 연구의 본질은 이 숫자 자체가 아니라 **국소 구간에서 찾은 증거를 장시간 기록의 판정으로 연결하는 흐름**이다 [CLM-035, CLM-042].

### 2.1.1 개별 심박을 분류하는 SNN 연구

Amirshahi와 Hashemi는 R-peak 전 0.25초와 후 0.45초를 잘라 **심박 하나**를 입력으로 사용하였다[3]. 심박의 진폭을 푸아송 스파이크 열(Poisson spike train)로 바꾸고, STDP 계층이 스파이크 발생 시점에서 심박 형태를 학습한다. 마지막 R-STDP 계층은 정답이면 보상, 오답이면 벌점을 받아 그 심박의 클래스를 정한다.

이 연구가 묻는 질문은 **“지금 들어온 한 번의 심박은 어떤 종류인가?”**이다. 반면 본 연구는 한 심박의 판정으로 끝나지 않는다. 연속 ECG를 여러 Snapshot으로 관찰한 뒤, 일부 구간에서 나타난 질환 증거를 모아 **기록 전체가 어느 클래스인지** 판정한다. 따라서 SNN을 사용한다는 공통점은 있지만 최종 판정의 범위가 심박 하나와 장시간 기록 전체로 다르다 [CLM-036].

### 2.1.2 연속 ECG에서 변화가 생긴 순간을 처리하는 연구

**사건 구동형(event-driven)**이란 ECG 숫자를 매번 똑같이 처리하는 대신, 파형이 기준보다 크게 변한 순간을 하나의 ‘사건’으로 만들어 처리하는 방식이다. 파형이 거의 움직이지 않으면 새 사건이 적게 발생하고, QRS처럼 짧은 시간에 크게 오르내리면 여러 사건이 발생한다. 즉 원래 파형 전체를 계속 계산하기보다 **의미 있는 변화가 생긴 순간을 중심으로 처리하는 방식**이다.

Bauer, Muir와 Indiveri는 연속 ECG를 이러한 사건 신호로 바꾸고 뉴로모픽 처리기에서 감시하였다[4]. 처리기는 평소와 다른 병리 패턴이 나타나 판독값이 문턱을 넘으면 이진 검출 신호를 낸다. 쉽게 말해 이 연구가 답하는 질문은 **“지금 ECG에 평소와 다른 병리 패턴이 나타났는가?”**이다. 연속 ECG를 상시 감시한다는 점은 본 연구와 가깝지만, 최종 목표는 이상 구간을 알리는 것이다. 해당 장시간 기록을 NSR·CHF·ARR·AFF 가운데 하나로 분류하는 연구는 아니다 [CLM-037].

본 연구도 연속 ECG에서 강한 변화와 이상 구간을 찾지만 거기서 끝나지 않는다. 어떤 Snapshot에서 ARR 또는 AFF를 지지하는 증거가 나타났다면 그 증거를 장시간 판정에 남기고, 이후 구간에서 같은 증거가 다시 나타나는지 확인한다. 즉 Bauer 연구가 **이상 구간을 발견해 알리는 단계**에 초점을 둔다면, 본 연구는 **발견된 여러 구간의 질환 증거를 모아 기록 전체의 네 클래스를 구분하는 단계**까지 이어진다.

Chen, Tian, Yang과 Sawan은 레벨 교차 ADC(level-crossing ADC, LC-ADC)를 사용하였다[5]. ECG가 미리 정한 전압 단계를 넘어설 때만 상승 또는 하강 스파이크를 만들고, 스파이킹 합성곱 신경망이 이를 받아 N·SVEB·VEB·F 가운데 **개별 심박의 종류**를 정한다. 이 연구의 중심은 변화가 생겼을 때만 입력을 만들고 한 심박을 효율적으로 분류하는 것이다. Bauer 연구처럼 단순 이상 알림만 내는 것은 아니지만, 여러 시간 구간을 모아 장시간 기록 전체의 질환 클래스를 정하는 연구도 아니다 [CLM-038].

### 2.1.3 긴 ECG에서 일부 위험 구간을 집계하는 연구

Shanmugam, Blalock과 Guttag은 약 48시간 ECG에서 여러 연속 심박 구간을 만들고, 각 구간의 위험도를 계산하였다[6]. 전체 구간을 똑같이 평균하지 않고 위험도가 높은 상위 20%의 평균을 환자 단위 점수로 사용한다. 고위험 환자도 대부분의 심박은 정상처럼 보일 수 있지만 일부 병리적 구간이 더 자주 나타날 것이라는 생각이다.

이 연구는 **대부분 정상인 긴 기록에서 일부 중요한 구간을 찾아 전체 결과로 연결한다**는 점에서 본 연구와 방향이 매우 가깝다. 차이는 최종 질문이다. Shanmugam 연구는 **“이 환자의 향후 심혈관 사망 위험이 높은가?”**를 예측한다. 본 연구는 미래 위험도를 예측하는 대신 **“현재 ECG 기록은 NSR·CHF·ARR·AFF 중 어느 클래스인가?”**를 판정한다 [CLM-039].

### 2.1.4 가변 길이와 24시간 Holter의 상위 시간 통합

Zihlmann, Perekrestenko와 Tschannen은 9–61초 길이의 단일유도 ECG를 정상 리듬, 심방세동 리듬, 기타 리듬, 잡음 기록의 네 클래스로 분류하였다[7]. CNN이 짧은 구간의 특징을 찾고, 시간 평균 또는 양방향 LSTM이 그 특징을 하나로 모아 기록의 클래스를 정한다.

이 연구는 ECG를 네 클래스로 나누는 연구가 이미 존재한다는 점을 보여준다. 다만 입력 자체가 9–61초의 짧은 기록이므로, 대부분 정상인 수시간 Holter에서 드물게 나타난 질환 구간을 찾아 장시간 판정으로 연결하는 문제가 중심은 아니다. 따라서 본 연구의 차별성은 단순히 **“네 클래스를 분류한다”**가 아니라, **긴 연속 기록에서 일부 질환성 구간을 포착하고 그 반복을 기록 전체 판정에 반영한다**는 데 있다 [CLM-040].

2026년에 발표된 DeepHHF의 정식 논문명은 “Modeling day-long ECG signals to predict heart failure risk with explainable AI”이다[8]. 이 연구의 처리 흐름은 다음과 같다.

1. 24시간 Holter ECG를 30초 구간으로 나눈다.
2. 각 30초 구간에서 심박과 파형의 특징을 하나의 요약 정보로 만든다.
3. Transformer가 시간 순서대로 놓인 여러 구간의 요약 정보를 함께 본다.
4. 마지막에 해당 환자가 5년 안에 심부전으로 진행할 위험 점수를 출력한다.

DeepHHF는 **긴 ECG를 짧은 구간으로 나누고, 구간별 정보를 다시 장시간 결과로 합친다**는 점에서 검토한 연구 가운데 본 연구와 구조적 흐름이 가장 유사하다. 따라서 “짧은 구간을 순차적으로 모아 장시간 결과를 만든다”는 발상 자체를 본 연구만의 최초성으로 주장할 수는 없다.

두 연구가 갈라지는 지점은 최종적으로 답하는 질문이다. DeepHHF는 **“이 환자가 앞으로 5년 안에 심부전으로 진행할 위험이 얼마나 큰가?”**를 묻는 예후 예측 연구다. 본 연구는 **“현재 들어온 ECG 기록이 NSR·CHF·ARR·AFF 가운데 어느 클래스인가?”**를 묻는 현재 기록 분류 연구다. 또한 DeepHHF는 실제 24시간 Holter를 사용했지만 본 연구의 현재 검증 입력은 공개 데이터 길이 제약에 따른 30분이다. 즉 장시간 구간 통합이라는 큰 흐름은 유사하지만, 예측 대상과 최종 출력이 다르며 본 연구는 아직 24시간 성능을 검증하지 않았다 [CLM-035, CLM-041, CLM-042].

### 2.1.5 선행연구 비교와 본 연구의 위치

| 연구 | 이 연구가 묻는 핵심 질문 | ECG를 보는 범위 | 최종 출력 | 본 연구와의 거시적 관계 |
|---|---|---|---|---|
| Amirshahi–Hashemi[3] | 지금 심박 하나는 어떤 종류인가? | R-peak 주위 한 심박 | 개별 심박 클래스 | 본 연구는 한 심박이 아니라 장시간 기록 전체를 판정한다. |
| Bauer et al.[4] | 지금 병리적 패턴이 나타났는가? | 연속 ECG | 이상 구간 이진 검출 신호 | 연속 감시는 유사하지만 질환별 기록 클래스를 정하지 않는다. |
| Chen et al.[5] | 변화가 생겼을 때 이 심박은 어떤 종류인가? | 개별 심박 | N·SVEB·VEB·F 심박 클래스 | 사건 기반 입력은 유사하지만 장시간 기록을 판정하지 않는다. |
| Shanmugam et al.[6] | 이 환자의 향후 심혈관 사망 위험이 높은가? | 약 48시간 ECG | 환자 단위 위험도 | 중요한 일부 구간을 모으는 방향은 유사하지만 목적은 미래 위험 예측이다. |
| Zihlmann et al.[7] | 이 짧은 ECG 기록은 네 리듬 범주 중 무엇인가? | 9–61초 ECG | 정상·AF·기타·잡음 | 네 클래스 기록 분류는 존재하지만 장시간의 간헐 구간 탐색이 중심은 아니다. |
| DeepHHF[8] | 이 환자가 5년 안에 심부전으로 진행할 위험은 얼마인가? | 24시간 Holter | 5년 HF 위험 점수 | 구간 분할과 장시간 통합 흐름은 가장 유사하지만 예후 예측이 목적이다. |
| 본 연구 | 이 장시간 ECG 기록은 NSR·CHF·ARR·AFF 중 무엇인가? | 현재 30분, 24시간 지향 | 기록 단위 네 클래스 | 간헐적 질환 구간을 포착하고 반복 증거를 모아 현재 기록의 클래스를 정한다. |

*표 2. 대표 관련 연구가 최종적으로 답하는 질문을 중심으로 한 비교. 과업·데이터셋·입력 길이·출력 단위가 서로 달라 정확도 순위 비교에는 사용할 수 없다. [근거: EXT-009~EXT-014; CLM-036~CLM-042; `docs/RELATED_WORK_HOLTER_ECG_KR.md`]*

거시적으로 보면 선행연구는 네 방향으로 나뉜다. 첫째, 심박 하나의 종류를 분류한다. 둘째, 연속 ECG에서 이상이 나타난 순간을 알려 준다. 셋째, 긴 기록의 일부 위험 구간을 모아 환자의 미래 위험도를 예측한다. 넷째, 여러 짧은 구간을 시간 순서대로 통합해 장시간 예후를 예측한다. 본 연구는 이 가운데 **이상 구간 탐지와 장시간 구간 통합을 기록 단위 다중 클래스 분류로 연결하는 방향**에 위치한다. 연속 ECG에서 질환성이 강한 Snapshot을 찾고, 그 증거의 강도·빈도·반복성과 지속성을 모아 전체 기록의 NSR·CHF·ARR·AFF 클래스를 판정한다 [CLM-042].

검토한 대표 선행연구 범위에서는 **간헐적 질환 구간을 찾고 그 반복 증거를 모아 NSR·CHF·ARR·AFF 기록 클래스를 판정하는 목적**과 MATLAB–XMODEL–RTL–FPGA 검증 흐름을 함께 적용한 사례를 확인하지 못하였다. 이는 문헌 전체에 동일 연구가 없다는 최초성 단정이 아니라, 위 여섯 편의 대표 원 논문과 공식 출판 경로를 기준으로 한 제한된 비교다 [CLM-042].

이 위치에서 도출한 설계 요구는 다음과 같다. 장시간 입력은 전체를 저장하지 않고 순차 Snapshot으로 처리하며, 정상으로 보이는 다수 구간 속에서도 질환성이 강한 Snapshot을 버리지 않아야 한다. 각 Snapshot의 증거 강도뿐 아니라 출현 횟수, 반복성과 장시간 일관성을 클래스별 상태에 남기고, 마지막에 기록 단위 판정으로 결합해야 한다. 현재 60초 Snapshot×30=30분은 공개 데이터셋 길이에 맞춘 구현·검증 조건이다. 24시간 이상의 정확도, 실시간 처리시간과 전력은 아직 검증하지 않았다 [CLM-035, CLM-042].

이 요구를 구현한 전체 신호 흐름은 다음과 같다.

전체 신호 흐름은 `공개 ECG → MATLAB 공칭 AFE+ADC → SystemVerilog XMODEL → 1 kSPS signed 12-bit stream → 사건·상태형 디지털 코어 → RTL/IP/FPGA 재생`이다. MATLAB은 공칭 필터·이득·ADC 범위와 기준 벡터를 제공한다. XMODEL은 전원선 간섭, 기준선 변동, 부품 오차, 연산증폭기와 ADC 비이상성을 모델로 검토하고 장시간 부호 스트림을 만든다. 디지털 코어는 이 스트림을 표본값 단위로 받아 Snapshot과 Final Membrane을 계산한다.

![그림 2. 전체 연구·검증 workflow](../figures/final/FIG-02_overall_workflow.svg)

*그림 2. 공개 ECG와 MATLAB 사전검증 이후 XMODEL과 디지털 RTL 개발로 나뉘고, AFE–RTL 통합·가속기 성능 비교·FPGA 구현 검증이 하나의 설계·통합 판단 단계로 모인다. 기준을 충족하지 못하면 모델·RTL 구현을 수정해 다시 검증하고, 충족하면 잠금 최종시험과 보고서 작성으로 진행한다. 잠금 최종시험은 수정 loop 밖에 있으며 결과를 설계에 되먹임하지 않는다. 아날로그 계층은 모델 기반이며 물리 측정 결과가 아니다. [근거: CLM-007, CLM-012, CLM-013, CLM-028; `source_of_truth/upstream_commits.yaml`; `components/digital_accelerator/configs/final_submission_locked_model.json`; `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv`]*

이 workflow에 적용되는 중요한 평가 원칙은 **설계·검증 반복과 최종 성능 평가의 분리**다. MATLAB에서는 공칭 필터·이득·동적 범위와 기준 벡터를 확인하고, XMODEL에서는 간섭과 비이상성 및 signed stream 인계를 확인한다. 이후 정수 reference와 RTL의 기능 일치, FPGA 통합의 `final_pred`·`final_mem` 일치를 차례로 점검한다. 이 과정에서 발견된 구현 오류는 해당 단계에서 수정할 수 있지만, 잠금 이후 한 번 수행한 final-test 결과로 AFE 파라미터나 RTL 판정 구조를 다시 조정하지 않는다.

인계의 기준 인터페이스는 표 3과 같다. `sample_valid && sample_ready`가 참인 클록에서만 한 표본값을 수락한다. XSim 통합에서는 수락된 표본값 사이에 canonical `sample_gap_cycles=2`를 사용한다. 이 클록 간격은 1 kSPS라는 실제 입력 표본률과 다른 개념이며 가속기 처리량 수치도 아니다.

| 항목 | 기준 규약 | 의미 |
|---|---:|---|
| 입력 표현 | signed 12-bit two’s-complement | AFE/ADC 모델과 디지털 코어의 코드 규약 |
| 입력 표본률 | 1,000표본/s | 한 표본값 간격 1 ms |
| Snapshot | 수락 표본값 60,000개 | 60초 국소 상태 확정 |
| Final decision | Snapshot 30개 | 1,800,000표본=30분 |
| XSim 입력 간격 | `sample_gap_cycles=2` | 보드 대상 기준 검증 조건 |
| 출력 | `final_pred`+4개 `final_mem` | 클래스 승자와 내부 부호 있는 최종 상태 |

*표 3. 전체 인터페이스 규약. [근거: CLM-002, CLM-003, CLM-013; `components/digital_accelerator/reports/final/digital_input_contract.md`]*

## 2.2 데이터셋과 평가 프로토콜

네 클래스는 서로 다른 PhysioNet 데이터베이스에서 왔다. 원시 파형은 공개 Git에 포함하지 않고 version 1.0.0, DOI, 원 표본률, 사용 record와 예상 SHA256를 manifest로 고정한다. 내려받기·검증 도구는 저장소 밖에 원본을 복원하며 ODC-By 1.0 표시와 데이터베이스별 인용 조건을 따른다[9]–[14].

| 클래스 | 원천/version | 원 표본률 | DOI | 최종 시험 record 수 |
|---|---|---:|---|---:|
| NSR | nsrdb 1.0.0 | 128 Hz | 10.13026/C2NK5R | 5 |
| CHF | chfdb 1.0.0 | 250 Hz | 10.13026/C29G60 | 4 |
| ARR | mitdb 1.0.0 | 360 Hz | 10.13026/C2F305 | 9 |
| AFF | afdb 1.0.0 | 250 Hz | 10.13026/C2MW2D | 1 |

*표 4. 데이터셋 원천과 최종 시험 record 구성. [근거: EXT-003~EXT-008; 데이터셋 manifest·license]*

**왜 30분인가.** 24/48시간 Holter가 본 연구의 장시간 관찰 동기지만, 원천 데이터베이스의 record 길이는 동일하지 않다. 제한 조건은 ARR 원천인 MIT-BIH Arrhythmia Database의 30분 excerpt다[2], [11]. 따라서 모든 클래스가 실제로 보유한 같은 시간 범위를 비교하고, 특정 클래스에만 padding·반복·추정 데이터를 만들지 않도록 `60초 Snapshot × 30개 = 30분`을 학습·검증·최종 시험과 FPGA 재생의 공통 창으로 고정하였다 [CLM-035]. 이는 데이터셋 제약 아래 선택한 공학적 평가 단위이지, 30분이 임상 Holter의 충분한 관찰 시간이라는 주장이 아니다.

각 원천 데이터는 공통 1 kSPS signed 12-bit 규약으로 변환되지만 이것이 유도·장비·대상군·잡음 차이를 제거했다는 뜻은 아니다. 클래스와 데이터베이스가 일대일로 결합되므로 database–class confounding이 남는다 [CLM-017]. 고정 버전 원시 파형은 저장소에 포함하지 않는다. 데이터셋 manifest·license·예상 SHA와 내려받기·검증 도구로 저장소 밖에 복원하고, 보고서에 쓰는 고정 파생 근거만 보존한다.

분할 단위는 `source_record_id`다. 한 원본 record에서 생성된 모든 30분 구간은 학습, 검증, 최종 시험 가운데 하나에만 속한다. 이 방법은 같은 record가 여러 partition에 섞이는 직접 누출을 막지만, 데이터베이스의 정체성과 클래스의 결합까지 해소하지는 않는다 [CLM-016].

| 분할 | 클래스별 30분 구간 | 전체 | 역할 |
|---|---:|---:|---|
| 학습 | 17×4 | 68 | 모델 적합 확인 |
| 검증 | 8×4 | 32 | Final Membrane 모델 선택 |
| 고정 최종 시험 | 9×4 | 36 | 고정 후 1회 평가 |
| 최종 시험 원본 record | 5/4/9/1 | 19 | record-majority 집계 단위 |

*표 5. 엄격한 원천 record 단위 분할. [근거: CLM-007, CLM-016; 고정 split 설정]*

고정 모델 `structural_guarded_silent_aff_1008710`은 학습·검증 결과로 선택한 뒤 문턱값·가중치·구조 보정 논리를 동결했다. 최종 시험은 모델 선택이나 파라미터 탐색에 사용하지 않았고 평가 횟수는 1, `test_used_for_selection=false`다 [CLM-007]. 정확도, macro F1, balanced accuracy와 클래스 재현율을 사용한다. Record-majority는 같은 최종 partition의 30분 구간을 원본 record별 다수결로 합친 값이므로 별도의 독립 시험이 아니다.

# 3. MATLAB 공칭 AFE·ADC 사전검증

공개 ECG를 곧바로 회로 모델이나 RTL에 넣기 전에, 먼저 MATLAB에서 앞단의 공칭 설계가 의도대로 동작하는지 확인하였다. 이 단계의 목적은 물리 회로를 측정하는 것이 아니라 필터 차단주파수, 계측증폭기 이득, 60 Hz 제거, ADC 동적 범위와 디지털 인계 형식을 수치와 기준 벡터로 고정하는 것이다. 여기서 정한 파라미터와 벡터가 다음 장의 AFE·ADC XMODEL 설계 기준이 된다.

## 3.1 MATLAB 사전검증의 역할과 흐름

MATLAB과 XMODEL은 같은 일을 반복하는 도구가 아니다. MATLAB은 공칭 R/C·이득·주파수 응답·ADC 동적 범위와 기준 벡터를 정의한다. XMODEL은 그 의도를 solver 기반 SystemVerilog 회로망으로 구현하고, 전원선 간섭·offset·baseline wander·R/C mismatch·유한 GBW/VOS·ADC 비이상성과 장시간 스트림을 검토한다. 즉 `MATLAB 공칭 기준 → XMODEL 비이상성 검증 → signed stream → locked RTL` 순서로 역할이 이어진다.

![그림 3. MATLAB pre-validation의 프로젝트 내 역할](../figures/final/MAT-07_prevalidation_flow.png)

*그림 3. 고정 MATLAB component의 pre-validation 흐름. XMODEL 전 공칭 기준을 정의하는 단계이지 MATLAB-XMODEL bit-exact 완료를 뜻하지 않는다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_matlab_prevalidation_flow.png`; `components/matlab_prevalidation/README.md`]*

## 3.2 공칭 주파수응답과 동적 범위 검증

MATLAB은 각 블록의 bilinear-equivalent filter와 IA ×201을 결합해 공칭 응답을 계산한다. 10 Hz 전체 이득은 46.0269 dB이며 5 Hz와 40 Hz는 각각 10 Hz 기준 −0.00984 dB, −0.57908 dB다. HPF cutoff 0.4823 Hz는 10 Hz 기준 −2.9733 dB, LPF 150 Hz는 −3.2552 dB다. 이 값의 절대 dB에는 IA ×201이 포함되므로 0.05 Hz의 절대값만 보고 기준선이 증폭된다고 해석하지 않고 통과대역 상대값을 함께 본다.

대표 NSR·CHF·ARR·AFF 60초 record에서는 ADC rail에 닿은 표본이 모두 0%였고, 가장 작은 rail 여유는 ARR의 1.019633440086 V였다 [CLM-015, CLM-024]. 그림 4는 클래스별 최소 headroom, 그림 5는 offset-binary code가 0·4095 rail에서 떨어져 분포하는 모습을 보여준다.

| 클래스 | AFE 출력 범위 | ADC 코드 범위 | 잘림 비율 | 최소 rail 여유 |
|---|---:|---:|---:|---:|
| NSR | −0.111193~0.385184 V | 1909–2525 | 0% | 1.264815619462 V |
| CHF | −0.278713~0.557422 V | 1701–2739 | 0% | 1.092577998716 V |
| ARR | −0.630367~0.466399 V | 1265–2626 | 0% | 1.019633440086 V |
| AFF | −0.350374~0.326538 V | 1612–2452 | 0% | 1.299625888976 V |

*표 6. MATLAB 공칭 동적 범위. 선택한 네 record의 모델 결과이며 전체 대상군이나 물리 rail 측정값이 아니다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv`; CLM-015, CLM-024]*

![그림 4. 대표 네 클래스의 ADC headroom](../figures/final/MAT-04_dynamic_range_headroom.png)

*그림 4. 고정 MATLAB component의 대표 클래스별 최소 rail 여유. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_dynamic_range_headroom.png`; `components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv`]*

![그림 5. 대표 ECG의 offset-binary ADC code 분포](../figures/final/MAT-05_adc_code_distribution.png)

*그림 5. 네 대표 입력의 ADC 코드 분포. 이 그림의 x축은 ADC 물리 규약 확인용 offset-binary이고 RTL canonical 입력은 signed two’s-complement다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_adc_code_distribution.png`; `components/matlab_prevalidation/matlab_afe_validation/results_dataset/adc_code_mapping_test.csv`]*

## 3.3 기준 벡터 생성과 XMODEL 인계

MATLAB은 클래스마다 `input.csv`, 단계별 `matlab_stage_outputs.csv`, ADC 물리 규약 확인용 `adc_offset_binary.mem`, signed 수치 확인용 `adc_signed.txt`, 공식 replay용 `adc_signed_twos_complement.mem`을 만든다. 네 클래스×5개 파일의 byte 수와 SHA256은 manifest로 고정되고, LF line ending과 3자리 대문자 hex 형식까지 검사한다. 그림 6은 이 기준 벡터가 XMODEL 비교와 locked RTL replay로 이어지는 순서를 보여준다.

![그림 6. MATLAB 기준 벡터 인계](../figures/final/MAT-06_reference_vector_handoff.png)

*그림 6. 고정 MATLAB component의 reference-vector handoff. 공식 replay 파일은 `adc_signed_twos_complement.mem`이다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_reference_vector_handoff.png`; `components/matlab_prevalidation/matlab_afe_validation/reference_vectors/reference_vector_manifest.csv`; `components/matlab_prevalidation/matlab_afe_validation/docs/MATLAB_TO_XMODEL_HANDOFF.md`]*

# 4. AFE·ADC 회로 설계와 XMODEL 검증

MATLAB에서 확인한 공칭 설계값을 SystemVerilog XMODEL의 회로망과 ADC 모델로 옮겼다. 이 장은 각 블록이 필요한 이유와 실제 R/C·이득·양자화 값을 먼저 설명하고, 이어서 공칭 계산만으로 확인할 수 없는 부품 오차, 전원선 간섭, 유한 GBW와 입력 offset, ADC 비이상성과 장시간 스트림을 검증한다.

## 4.1 AFE·ADC 신호 경로와 회로 설계

디지털 분류기 앞단의 목적은 공개 ECG 전압을 증폭만 하는 것이 아니라, 기준선 이동과 전원선 간섭을 줄이고 1 kSPS signed 12-bit 스트림으로 일관되게 넘기는 것이다. 현재 고정 component에는 README가 언급하는 LTspice `.asc`와 원본 회로 캡처가 실제로 포함되어 있지 않다. 따라서 그림 7은 원본 schematic이 아니라 MATLAB 파라미터 문서와 SystemVerilog XMODEL 정본에서 확인한 신호 순서만 크게 정리한 설명용 signal flow다. 세부 설계값과 비이상성 검증은 이어지는 본문과 표에서 설명한다. 누락된 원본은 `source_of_truth/unresolved_artifacts.csv`에 기록하며, 본문은 이 그림을 제작된 회로도 또는 실제 회로 증거로 사용하지 않는다 [CLM-034].

![그림 7. Analog AFE·ADC signal flow](../figures/final/FIG-15_analog_signal_flow_nonideal_models.svg)

*그림 7. ECG+와 ECG−가 각각 HPF를 통과한 뒤 3-op-amp IA에서 합류하고, 60 Hz notch·150 Hz LPF·ADC·signed stream으로 이어지는 analog signal flow. 상단은 `Input Disturbance Injection`, `R/C Tolerance & Op-Amp Error Model`, `ADC Error Model`로 구분하며, 하단 범례는 실선을 신호 경로로, 점선을 주입 교란 또는 비이상 모델로 정의한다. 원본 LTspice schematic이 아니다. 실제 PCB·silicon·post-layout 결과를 뜻하지 않는다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/docs/afe_adc_parameter_reference.md`; `components/afe_xmodel/analog/ecg_afe_xmodel.sv`; `source_of_truth/unresolved_artifacts.csv`]*

전체 경로는 `ECG 입력 → HPF → 3-op-amp IA → active Twin-T 60 Hz notch와 buffer → 150 Hz LPF와 buffer → 12-bit ADC → offset-binary → signed two’s-complement stream`이다 [CLM-028]. 그림 8은 같은 순서를 MATLAB 공칭 모델 관점에서 보여준다.

![그림 8. MATLAB 공칭 AFE·ADC chain](../figures/final/MAT-01_afe_chain_overview.png)

*그림 8. 고정 MATLAB component의 `fig_afe_chain_overview`. 공칭 블록 순서를 보여주는 기준 그림이며 XMODEL 비이상성이나 물리 회로 측정을 뜻하지 않는다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_afe_chain_overview.png`; `components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md`]*

### 4.1.1 기준선 이동을 이득단 전에 제거하는 HPF

**왜 필요한가.** ECG에는 원하는 박동 성분 외에 전극 DC offset과 느린 기준선 이동이 포함될 수 있다. 이 성분을 ×201 IA에 먼저 넣으면 신호보다 offset이 크게 증폭되어 rail 여유를 소모한다. 따라서 양·음 전극 경로 각각에 HPF를 두고 IA 앞에서 DC와 느린 변화를 줄인다.

**어떻게 구성했는가.** 각 차동 입력은 33 nF 직렬 커패시터를 지나고, 출력 노드는 10 MΩ 저항으로 0 V 기준에 연결된다. 두 입력에 같은 구조를 사용하여 차동 경로를 보존한다. 초기 버전에서 음전극 커패시터가 접지 쪽으로 잘못 연결되어 차동 입력과 CMRR 검증이 불가능했던 문제도 XMODEL 정본에서 `ana_neg→C2→n_hpfn` 경로로 수정하였다.

**어떤 값으로 설계했는가.** 차단주파수는 `fc=1/(2πRC)=1/(2π×10 MΩ×33 nF)=0.482287706339 Hz`다. 시정수는 330 ms이고 약 5τ인 1.65 s 뒤에 정착하므로 XMODEL 비교는 일반적으로 앞 2 s를 제외한다.

**무엇을 검증했고 다음 블록에 어떻게 연결되는가.** XMODEL offset 시험에서 ±200 mV를 인가해도 정착 뒤 clipping은 0이었고, 0.1 Hz 1 mV와 0.2 Hz 2 mV 기준선 이동은 차단주파수에 따라 서로 다른 잔류를 보였다. 이 결과는 HPF가 모든 저주파 성분을 완전히 지운다는 뜻이 아니라, 큰 DC offset을 IA 이득 전에 줄인다는 것을 보여준다. HPF의 두 출력은 다음 3-op-amp IA의 비반전 입력으로 들어간다.

### 4.1.2 작은 차동 ECG를 ×201로 키우는 3-op-amp IA

**왜 필요한가.** mV 수준 ECG를 ±1.65 V ADC 범위에서 충분한 코드 변화로 변환하면서 양 전극에 함께 들어오는 공통모드 간섭은 억제해야 한다. 이를 위해 입력 임피던스와 CMRR에 유리한 3-op-amp 계측증폭기 구조를 사용한다.

**어떻게 구성했는가.** U1·U2의 두 비반전 증폭기는 100 kΩ 피드백 저항 두 개와 그 사이 1 kΩ 이득 저항을 사용한다. 뒤의 U3 차동증폭기는 R5·R7·R8·R9를 모두 10 kΩ으로 두어 U1·U2 출력 차이를 단일 출력으로 바꾼다. 2단 차동증폭기 이득은 1이므로 전체 이득은 1단과 같다.

```text
Av_IA = 1 + 2Rfb/Rg
      = 1 + 2×100 kΩ/1 kΩ
      = 201 V/V
```

**실제 설계에서 무엇을 수정했는가.** 초기 XMODEL의 이산 relaxation op-amp는 3-op-amp 피드백망에서 차동모드가 수렴하지 않아 ADC가 1939 부근에 고정되었다. 정본은 `vcvs` 회로 solver primitive로 개루프 차동·공통모드 이득을 표현해 폐루프 ×201을 회복하였다. op-amp CMRR 설정도 경계값 100 dB에서 110 dB로 올려 목표보다 모델 여유를 두었다. 이 110 dB는 소자 실측 CMRR이 아니며 실제 영향은 저항비 오차에 제한된다.

**무엇을 검증했고 다음 블록에 어떻게 연결되는가.** XMODEL 주파수 특성에서 통과대역 이득은 약 200으로 목표 201의 약 99%였다. worst-direction R/C mismatch에서는 0.1%에서 CMRR 100.7 dB, 1%에서 80.0 dB였고 1%에서도 60 Hz 잔류 ≤6.54 mV와 clipping 0을 확인했다 [CLM-026]. IA 출력은 active Twin-T의 두 T 경로에 동시에 들어간다.

### 4.1.3 60 Hz만 선택적으로 줄이는 active Twin-T와 buffer

**왜 필요한가.** 전극선에 유입되는 60 Hz 전원선 간섭은 IA를 통과한 ECG에 겹칠 수 있다. 단순 LPF만으로 60 Hz를 충분히 줄이려 하면 QRS 형태에 필요한 대역까지 손상될 수 있으므로 60 Hz 부근만 좁게 억제하는 notch가 필요하다.

**어떻게 구성했는가.** Twin-T의 저항 경로는 `R–R–2C`, 커패시터 경로는 `C–C–R/2`로 구성한다. 기준값은 R=26.526 kΩ, C=100 nF이므로 RT1=RT2=26.526 kΩ, CT=200 nF, CB1=CB2=100 nF, RB=13.263 kΩ이다. 60 Hz에서 두 경로가 반대 위상으로 만나 상쇄되도록 했다.

**수동 구조에서 왜 변경했는가.** 수동 Twin-T는 Q가 약 0.25로 낮고 출력 임피던스가 높다. 여기에 후단 1 kΩ LPF가 직접 연결되자 notch 출력이 loading되어 실효이득이 36까지 낮아졌고, 수동 notch를 포함한 전체 −3 dB 대역폭도 약 17 Hz로 줄었다. 정본은 notch 뒤 unity buffer를 추가하여 1 kΩ LPF를 격리하고, buffer 출력의 95%를 CT·RB 공통 노드에 되먹이는 active Twin-T로 변경하였다. Rk1=5 kΩ, Rk2=95 kΩ이므로 `k=Rk2/(Rk1+Rk2)=0.95`, `Q≈1/[4(1−k)]=5`다.

**무엇을 검증했고 다음 블록에 어떻게 연결되는가.** MATLAB nodal dense sweep은 30–100 Hz 범위에서 60 Hz −83.5557 dB, local −3 dB bandwidth 11.721 Hz, 추정 Q 5.119를 보였다. 50 Hz 감쇠는 −1.131 dB이므로 50 Hz까지 제거한다고 해석할 수 없다 [CLM-029]. XMODEL 특성시험에서도 60 Hz notch 약 80 dB와 150 Hz 전체 대역폭을 확인했다. 그림 9의 전체 응답에서 60 Hz ideal zero는 시간영역 디지털 근사의 표시값이고, analog-style notch 수치는 그림 10의 active Twin-T dense sweep을 사용한다.

![그림 9. MATLAB 공칭 전체 주파수 응답](../figures/final/MAT-02_total_frequency_response.png)

*그림 9. HPF·IA·디지털 notch 근사·LPF를 결합한 MATLAB 공칭 전체 응답. 60 Hz ideal zero는 물리 감쇠량이 아니다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_total_frequency_response.png`; `components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_frequency_response_metrics.csv`]*

![그림 10. Active Twin-T dense sweep](../figures/final/MAT-03_notch_dense_sweep.png)

*그림 10. active Twin-T의 MATLAB nodal dense sweep. 60 Hz 공칭 중심과 bandwidth/Q를 보여주지만 측정된 물리 Q는 아니다. [직접 근거: `components/matlab_prevalidation/matlab_afe_validation/figures/fig_notch_dense_sweep.png`; `components/matlab_prevalidation/matlab_afe_validation/results_dataset/notch_dense_sweep_metrics.csv`]*

### 4.1.4 150 Hz LPF, 12-bit ADC와 signed stream 변환

**왜 필요한가.** notch 뒤에는 1 kSPS ADC의 Nyquist 주파수보다 높은 성분과 EMI를 줄이는 LPF가 필요하다. 이어지는 ADC는 연속 전압을 디지털 RTL이 받는 고정 폭 코드로 바꾸어야 한다.

**어떻게 구성했고 어떤 값으로 설계했는가.** LPF는 1 kΩ과 1.06 µF의 1차 RC 구조이며 `fc=150.146172728 Hz`다. 초기 1 µF 값은 약 159 Hz였으므로 1.06 µF로 수정하였다. LPF 뒤 unity buffer가 ADC 입력을 구동한다. ADC 모델은 ±1.65 V의 3.3 V span, 12 bit, 1 kSPS이며 `LSB=3.3/4095=0.000805860805861 V`다 [CLM-028].

```text
offset_binary = floor((Vin + 1.65)/3.3 × 4095), 0…4095로 제한
signed_decimal = offset_binary − 2048
two's-complement hex = mod(signed_decimal, 4096), 한 줄당 3자리
```

floor 방식 때문에 0 V는 offset-binary 2047, signed −1(`FFF`)에 대응하고 +1 LSB 부근이 2048, signed 0(`000`)에 대응한다. 따라서 offset-binary 파일을 signed 입력 포트에 직접 넣지 않는다. XMODEL은 1 kHz `clk_samp`의 하강 edge에서 양자화한다. 초기 testbench는 같은 edge에서 nonblocking 갱신 전 값을 `$fdisplay`로 기록해 ADC log가 한 표본 밀렸다. 정본 testbench는 timestep 종료에 갱신값을 읽는 `$fstrobe`와 지연 기록 완료 뒤 file close를 사용하여 off-by-one을 수정하였다 [CLM-030]. 최종 출력은 1 kSPS signed 12-bit two’s-complement `.mem`으로 변환되어 디지털 RTL에 전달된다.

## 4.2 XMODEL 비이상성 및 설계 수정 검증

XMODEL의 첫 역할은 MATLAB 공칭 의도를 solver 기반 회로망으로 옮기는 것이다. 36개 60초 구간에서 앞 3 s 정착부를 제외하고 emulator와 비교한 평균 RMS 차이는 1.95 LSB, lag는 0이었다. 최대 편차는 QRS 급경사에서 30 LSB까지 나타났으므로 평균 파형 정합을 모든 표본의 bit-exact로 확대하지 않는다 [CLM-014].

두 번째 역할은 공칭 MATLAB에 없는 비이상성을 분리해 가하는 것이다. 전원선 간섭은 60 Hz에서 RMS 0.92 mV, 50 Hz에서 118 mV가 남았다. 이 설계의 target은 60 Hz이며 50 Hz에서는 center retuning과 별도 system 검증이 필요하다 [CLM-025]. R/C mismatch, GBW/VOS와 ADC 비이상성 결과는 표 7과 같다.

| XMODEL 검증 항목 | 직접 결과 | 해석 경계 |
|---|---:|---|
| Emulator↔XMODEL 36×60초 | 평균 RMS 1.95 LSB, lag 0, max ≤30 LSB | model-to-model 파형 정합; sample-wise bit-exact 아님 |
| 60/50 Hz PLI | 0.92 mV / 118 mV RMS 잔류 | 60 Hz target; 50 Hz retuned 성능 미검증 |
| R/C worst-direction mismatch | CMRR 100.7 dB@0.1%, 80.0 dB@1%; 1% 잔류 ≤6.54 mV | 직접 30분 mismatch `final_pred` sweep 아님 |
| finite GBW | 100 kHz에서 ideal 대비 2.04 code; clipping 0 | XMODEL dominant-pole model 범위 |
| 입력 VOS | 0.5/1/2 mV→출력 약 203/405/810 mV; 2 mV까지 clipping 0 | ×201 baseline 이동; 저 offset op-amp/DC servo 권장 |
| 분류 입력 60초 chunk clipping | train/val/test 1,200개 모두 0 | emulator/XMODEL-derived dataset; 실제 ADC 아님 |
| 전체 record 장시간 clipping | 35.9 billion sample에서 0.00007% | 모델로 만든 전체 길이 스트림; 물리 계측 아님 |
| R-peak/RR 보존 | shift 중앙값 1.0 ms, RR 오차 중앙값 0 ms | 공개 digitized ECG 기반 분석 |
| ADC non-ideal locked RTL | 대표 final_pred 15/16 유지 | 2 LSB rms noise의 NSR 한 건 flip; 보편 불변성 아님 |

*표 7. XMODEL 파형·교란·ADC 검증. 시험 단위가 서로 다르므로 하나의 “전체 강건성” 수치로 합치지 않는다. [직접 근거: `components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md`; `components/afe_xmodel/docs/afe_stress/clipping_report.csv`; `components/afe_xmodel/docs/afe_stress/rpeak_timing_test.csv`; `components/afe_xmodel/docs/afe_stress/adc_nonideal_finalpred_xsim.csv`; CLM-014, CLM-025~CLM-033]*

실제 설계 수정도 검증 결과에 포함된다. IA relaxation 미수렴은 `vcvs` solver 모델로, notch 출력 loading은 unity buffer로, 159 Hz LPF는 1.06 µF로, 경계 CMRR 설정은 110 dB로, ADC log off-by-one은 `$fstrobe`로 수정하였다. 수동 Twin-T가 17 Hz부터 통과대역을 훼손한 문제는 k=0.95 active Twin-T로 변경해 150 Hz 대역을 회복하였다 [CLM-030]. 이는 단순 최종 수치보다 “문제를 관측하고 회로 구조를 수정한 과정”을 보여주는 설계 근거다.

# 5. 디지털 가속기 IP 설계 및 구현

이 장은 입력 숫자 하나가 최종 클래스 상태로 바뀌는 순서에 맞춰 회로를 설명한다. 먼저 표본값·사건·막전위의 뜻을 정의하고, 박동·리듬 경로와 파형 형태 경로를 차례로 다룬다. 마지막에는 두 경로의 증거가 60초 Snapshot과 30분 Final Membrane에서 결합되는 과정을 정리한다.

## 5.1 핵심 개념과 다중 시간축 처리

AFE와 ADC를 통과한 ECG는 더 이상 종이에 그려진 곡선이 아니다. 디지털 블록이 받는 입력은 `... -18, -12, 5, 41, 96 ...`처럼 시간 순서대로 들어오는 부호 있는 숫자의 나열이다. 회로에는 이 숫자가 P파인지 QRS파인지 알려 주는 표지가 없다. 따라서 디지털 IP는 숫자의 움직임에서 먼저 “파형이 급하게 변했다”는 사건을 만들고, 여러 사건의 시간 관계를 이용해 박동과 리듬을 스스로 구성해야 한다.

**표본값(sample).** 숫자 나열에서 값 하나가 한 시점의 ECG 전압을 나타낸다. 이를 표본값이라고 한다. 본 설계는 초당 1,000개를 받으므로 새로운 표본값은 1 ms마다 하나씩 들어온다. 60초에는 60,000개, 30분에는 1,800,000개의 표본값이 들어온다.

**파형 변화 사건 신호.** 현재 표본값에서 직전 표본값을 빼면 두 시점 사이 변화량이 나온다. 변화량이 양수면 파형이 상승했고 음수면 하강했으며, 절댓값이 클수록 짧은 시간에 크게 변했다는 뜻이다. 회로는 변화량이 기준을 넘은 순간 한 클록 길이의 사건 신호를 만든다. 사건 신호는 “조건이 지금 발생했다”는 알림이지 원래 파형을 저장한 값은 아니다.

**막전위형 누적값(membrane state).** 생물학적 뉴런은 입력 자극을 막전위에 모으고, 막전위가 임계점에 도달하면 발화한 뒤 다시 초기 상태로 돌아간다. 본 설계는 이 생각을 레지스터와 덧셈기로 구현한다. 사건이 들어올 때마다 누적값을 올리고, 누적값이 문턱값(threshold)을 넘으면 한 클록의 스파이크를 출력한 뒤 누적값을 0으로 되돌린다.

**누설(leak).** 일반적인 LIF 뉴런은 시간이 지나면 누적값을 조금씩 줄인다. 서로 멀리 떨어진 사건은 영향이 약해지고, 짧은 시간에 연속해서 들어온 사건만 손실을 이겨 내고 발화하게 만들기 위해서다. 본 QRS 검출 RTL도 누설 연산을 지원한다. 다만 현재 고정 제출 설정에서는 QRS 누설값이 0이므로, 실제 제출 회로의 누적값은 사건 사이에서 감소하지 않는다. 따라서 본문에서는 LIF의 일반 원리와 현재 설정의 실제 동작을 구분한다.

**불응기(refractory period).** 하나의 QRS파 안에서는 큰 상승과 하강이 여러 번 나타날 수 있다. 첫 발화 뒤에도 사건을 계속 누적하면 같은 QRS파를 두세 개의 박동으로 잘못 셀 수 있다. 이를 막기 위해 박동을 검출한 직후에는 일정 수의 표본값 동안 누적을 중지한다.

**박동과 RR 간격.** QRS 막전위형 누적값이 문턱값을 넘으면 회로는 “박동을 하나 찾았다”는 신호를 한 클록 동안 낸다. 이것이 내부 박동(beat)이다. 첫 박동부터 다음 박동까지 몇 개의 표본값이 들어왔는지를 세면 RR 간격이 된다. 외부의 R-peak 정답표를 읽는 것이 아니라 회로가 스스로 검출한 두 박동 사이 시간을 재는 방식이다.

**Snapshot.** Snapshot은 이미지가 아니라 60초 동안 관찰한 결과의 요약이다. 60,000개의 표본값에서 박동이 몇 번 발생했는지, RR 간격이 얼마나 일정했는지, 파형 방향 전환·진폭·폭·에너지가 어떤 경향을 보였는지를 작은 계수와 클래스 누적값으로 압축한다.

**Final Membrane.** 한 번의 60초 결과만으로 30분 전체를 판단하지 않기 위해 Snapshot 30개의 결과를 다시 네 개의 장시간 클래스 누적값에 모은다. 이것이 Final Membrane이다. 어떤 특징이 클래스를 지지하면 해당 누적값을 올리고, 반대하면 내린다. 마지막에는 네 누적값 가운데 가장 큰 값을 고른다.

**왜 SNN-inspired인가.** 이 구조는 모든 표본값을 저장한 뒤 한꺼번에 행렬 연산을 하는 대신, 의미 있는 변화가 생겼을 때 사건을 만들고 그 사건을 막전위형 누적값에 더한다. 누적값, 문턱값, 발화, 초기화와 승자독식이라는 뉴로모픽 개념을 정수형 RTL로 옮겼기 때문에 SNN-inspired라고 부른다. 다만 학습된 심층 SNN, STDP, 온라인 학습, 생물물리 뉴런 시뮬레이션이나 생물학적 등가성을 주장하는 구조는 아니다.

![그림 11. 다중 시간축 구조](../figures/final/FIG-04_multitimescale_architecture.svg)

*그림 11. 1 ms 표본값, 박동, 60초 Snapshot, 30분 Final Membrane의 세 단계 상태 이동. [근거: CLM-003, CLM-023]*

![그림 12. 디지털 signal flow](../figures/final/FIG-12_digital_signal_flow.svg)

*그림 12. signed ECG는 `ΔECG Calculation`, `Strong-Event Detector`, `QRS LIF Neuron`을 거친다. 강한 변화 사건과 QRS LIF의 특징 출력은 서로 다른 선으로 유지되며, `Rhythm Feature Path`와 `Morphology Feature Path`는 `Feature Accumulation & Class Scoring`에서 처음 합류한다. `60 s Snapshot Membrane` 30개는 `30-Snapshot Accumulation`을 거쳐 `30 min Final Membrane`으로 누적되고 NSR·CHF·ARR·AFF 기록 클래스를 판정한다. 실제 합성 netlist 배선을 뜻하지 않는다.*

전체 흐름을 한 문장으로 연결하면 다음과 같다. 숫자로 들어온 ECG가 급하게 오르내리면 강한 사건이 생기고, 강한 사건이 충분히 모이면 박동이 된다. 박동 사이 표본 수는 RR 간격이 되고, 박동 주변 숫자의 움직임은 기울기 전환·진폭·폭·에너지 정보가 된다. 이 값들을 60초 동안 모아 Snapshot을 만들고, Snapshot 30개를 Final Membrane에 모아 최종 클래스를 고른다. 이는 회로 흐름을 설명하기 위한 예이지 실제 환자 진단 예가 아니다.

## 5.2 박동 및 리듬 정보 추출

![그림 13. 박동·리듬 경로](../figures/final/FIG-13_beat_rhythm_path.svg)

*그림 13. 인접 표본값 차이에서 박동, RR, PNN/RDM/early–late 증거로 이어지는 상태 전이. [근거: 고정 디지털 RTL `c6b80de...`]*

### 5.2.1 표본값에서 강한 상승과 하강 찾기

ECG의 절대 전압은 사람, 유도와 측정 환경에 따라 달라질 수 있다. 반면 현재 숫자에서 바로 앞 숫자를 뺀 변화량은 지금 파형이 얼마나 빠르게 상승하거나 하강하는지를 직접 보여 준다. 첫 번째 표본값은 비교 대상이 없으므로 직전 값 레지스터에 저장만 한다. 두 번째 표본값부터 매 클록 다음 계산을 반복한다.

```text
변화량 = 현재 표본값 - 직전 표본값
변화 크기 = |변화량|

변화량이 양의 기준보다 크면  → 상승 사건
변화량이 음의 기준보다 작으면 → 하강 사건
변화 크기가 강한 변화 기준보다 크면 → 강한 사건

계산이 끝나면 현재 표본값을 다음 비교의 직전 값으로 저장
```

상승·하강·강한 사건은 조건을 만족한 클록에서만 1이 되고 다음 클록에는 다시 0이 된다. 변화 기준은 처음부터 하나로 고정하지 않는다. 60초 구간의 초기 표본에서 12개의 변화 크기 후보를 각각 몇 번 넘는지 세고, 사건이 지나치게 많거나 적지 않은 후보를 선택한다. 선택이 끝나기 전에는 기본 문턱값을 사용한다. 뉴로모픽 관점에서는 이 한 클록 펄스를 “Strong Event 뉴런이 발화했다”고 해석할 수 있다. 다만 실제 RTL에는 별도의 Strong Event 막전위가 있는 것이 아니라 뺄셈기·절댓값·문턱 비교기가 이 펄스를 직접 만든다. 이렇게 만든 사건은 박동 검출과 파형 형태 분석 경로에 동시에 전달된다. 이 기능을 RTL에서는 `ecg_event_encoder_adaptive`가 담당한다.

### 5.2.2 여러 강한 변화를 하나의 박동으로 묶기

잡음 하나가 큰 변화량을 만들었다고 곧바로 박동이라고 판단하면 오검출이 늘어난다. 반대로 QRS파 안에서 발생한 상승과 하강을 각각 박동으로 세면 한 박동을 여러 번 세게 된다. 이를 막기 위해 강한 사건 출력을 QRS 막전위형 누적값에 연결한다. 뉴런 관점에서 보면 Strong Event 발화가 시냅스를 통해 QRS LIF 뉴런으로 들어오고, 사건 가중치가 시냅스 가중치 역할을 하는 구조다.

```text
1. 불응기가 남아 있으면 누적값을 0으로 유지하고 남은 시간을 1 줄인다.
2. 불응기가 아니면 이전 누적값에서 설정된 누설량을 뺀다.
3. 현재 클록에 강한 사건이 있으면 사건 가중치를 더한다.
4. 결과가 박동 문턱값 미만이면 다음 클록의 누적값으로 저장한다.
5. 문턱값 이상이면 박동 사건을 한 클록 발생시키고 누적값을 0으로 지운다.
6. 동시에 불응기 계수기를 채워 같은 QRS파의 후속 변화를 잠시 무시한다.
```

일반적인 LIF 설명에서는 시간에 따른 누설 때문에 가까이 모인 사건이 더 쉽게 발화를 만든다. 그러나 현재 고정 설정의 QRS 누설량은 0이다. 따라서 제출 회로에서는 강한 사건이 들어올 때 누적값이 증가하고, 문턱값을 넘은 뒤 초기화와 불응기가 중복 박동을 막는다. QRS파는 보통 여러 인접 표본에서 큰 변화를 만들기 때문에 실제 입력에서는 강한 사건이 짧은 구간에 모여 박동 사건을 만드는 경향이 있지만, 현재 설정의 누설이 그 시간 간격을 강제하는 것은 아니다. 이 기능을 RTL에서는 `qrs_lif_detector`가 담당한다.

### 5.2.3 두 박동 사이 시간 재기

첫 박동이 검출되면 0에서 시작하는 표본 계수기를 연다. 이후 새로운 표본값을 받을 때마다 계수기를 1씩 올린다. 다음 박동이 들어오면 현재 표본까지 포함한 계수값을 RR 간격으로 확정하고 계수기를 다시 0으로 만든다. 첫 박동은 앞선 박동이 없으므로 시간 측정의 시작점만 된다. 즉 RR 간격은 어려운 추상 상태가 아니라 “직전 박동 이후 들어온 표본값의 개수”다. 1 kSPS이므로 계수값 1,000은 약 1초에 해당한다.

### 5.2.4 다음 RR 간격의 반복성 보기

일정한 리듬이라면 연속된 RR 간격은 비슷한 값 주변에 모인다. 회로는 가능한 RR 간격을 나타내는 46개의 기준 눈금을 가지고 있다. 새 RR 간격이 들어오면 한 클록에 46개를 모두 비교하지 않고, 매 클록 기준 눈금 하나와의 차이를 계산한다. 지금까지 가장 차이가 작은 눈금과 오차만 저장하므로 큰 병렬 비교기를 만들지 않아도 된다. 같은 거리의 눈금이 두 개면 먼저 검사한 낮은 번호를 유지한다.

가장 가까운 눈금은 다음 박동을 위한 예상 RR 간격으로 기억한다. 실제 다음 RR 간격이 이 눈금의 허용 범위 안에 들어오면 “예상과 일치”, 밖이면 “예상과 불일치” 사건을 만든다. Snapshot은 60초 동안 일치와 불일치가 각각 몇 번 발생했는지를 센다. 여기서 PNN은 범용 probabilistic neural network가 아니라 고정된 RR 눈금 가운데 가장 가까운 값을 찾고 다음 간격을 비교하는 회로다. 이 기능을 RTL에서는 `pnn_rhythm_predictor`가 담당한다.

### 5.2.5 연속 RR 간격의 변화량 보기

앞의 회로가 예상 간격과의 일치 여부를 본다면, 이 경로는 현재 RR 간격과 바로 직전 RR 간격의 절대 차이를 구한다. 첫 RR은 비교할 값이 없으므로 직전 값으로 저장만 한다. 두 번째 RR부터 차이가 15개의 변화 수준 가운데 어디까지 넘었는지를 표시하고, 가장 높은 수준을 4비트 코드로 만든다. 계산이 끝나면 현재 RR을 다음 비교의 직전 값으로 바꾼다. 따라서 PNN은 “예상한 반복 간격을 따르는가”를, RDM은 “두 번의 연속 간격이 얼마나 달라졌는가”를 서로 다르게 답한다. 이 기능을 RTL에서는 `rdm_variability_neuron`이 담당한다.

### 5.2.6 짧은 간격과 긴 간격의 교대 찾기

회로는 최근 RR 간격을 천천히 따라가는 기준값을 하나 유지한다. 새 RR이 기준보다 충분히 짧으면 early, 충분히 길면 late로 표시한다. 정상 범위라면 이전 비정상 표시를 그대로 둔다. 직전 비정상 간격과 현재 비정상 간격이 early→late 또는 late→early처럼 서로 반대이면 한 번의 쌍 사건을 만든다. 매 RR마다 기준값은 현재 RR 방향으로 조금만 이동하므로 갑작스러운 한 간격이 기준 전체를 즉시 바꾸지 않는다. 60초가 새로 시작되면 기준과 이전 패턴을 지운다. 쌍 사건은 Snapshot의 리듬·파형 형태 점수와 30분 집계에 전달된다. 이 기능을 RTL에서는 `ectopic_pair_neuron`이 담당한다.

| 관찰 대상 | 필요한 이유 | 구체적인 하드웨어 처리 | 생성 상태 | 사용 위치 | 구현 모듈 |
|---|---|---|---|---|---|
| 파형 변화 | QRS 후보와 기울기 방향 | 직전 표본값과의 부호 있는 차분, 절댓값, 적응형 문턱 후보 | 상승/하강/강한 사건 | QRS·DSCR·QRS MAF·지연 경로 | `ecg_event_encoder_adaptive` |
| 박동 | 여러 변화 펄스를 한 박동으로 결합 | 이전 막전위→누설→사건 가산→문턱값, 불응기 감소 | `beat_spike`, QRS 막전위 | RR 및 박동 관찰 구간 시작 | `qrs_lif_detector` |
| RR 패턴 | 반복 간격의 일관성 | 46개 중심 순차 거리 탐색, 이전 승자의 다음 RR 예측 | 일치/불일치 스파이크 | Snapshot 클래스 상태 | `pnn_rhythm_predictor` |
| RR 변화량 | 연속 간격의 변동 크기 | 직전 RR과의 절대 차이, 15개 문턱 수준 | RDM 수준/코드 | Snapshot 계수기와 Final 집계 | `rdm_variability_neuron` |
| Early–late 조합 | 보상성 간격 패턴 | 적응 기준, 직전 비정상 패턴 유지 | 쌍 스파이크 | 파형 형태·리듬 기여 | `ectopic_pair_neuron` |

*표 8. 리듬 경로의 실제 상태 기구. 모듈 이름은 마지막 열의 구현 확인 정보다.*

**통합 해석 경계.** 이 경로의 박동, RR, PNN, RDM과 ectopic-pair는 고정 하드웨어 내부의 공학적 대리지표다. 임상 QRS annotation, 표준 HRV 지표, probabilistic neural network 또는 ectopic diagnosis와 동일하다고 주장하지 않는다. 이 제한은 각 블록마다 반복하지 않고 이 절 전체에 적용한다.

## 5.3 파형 형태 및 진폭 정보 추출

리듬만으로는 같은 간격 패턴 안의 파형 차이를 설명하기 어렵고, 파형 형태만으로는 장기 규칙성을 설명하기 어렵다. 따라서 박동 경로와 병렬로 기울기 방향 전환, 최대 진폭 코드, QRS 주변 폭·복잡도·에너지와 말단 지연을 추출한다.

![그림 14. 파형 형태 경로](../figures/final/FIG-14_morphology_path.svg)

*그림 14. DSCR·RAM·QRS MAF·RBBB-like 경로가 유한 상태로 파형을 압축하는 과정. [근거: 고정 디지털 RTL `c6b80de...`]*

### 5.3.1 파형이 꺾인 횟수 세기

QRS파의 모양을 알려면 전압이 단순히 높았는지만 보는 것이 아니라 상승하던 파형이 언제 하강으로 바뀌었는지도 보아야 한다. 그러나 원시 표본값 두 개만 바로 빼면 작은 잡음에도 방향이 자주 바뀔 수 있다. 그래서 회로는 입력을 천천히 따라가는 기준값을 하나 유지한다. 현재 표본값과 기준값의 차이를 구하고, 그 차이를 오른쪽으로 이동해 작은 갱신량으로 만든 뒤 기준값에 더한다.

```text
오차 = 현재 표본값 - 필터 기준값
기준 갱신량 = 오차를 정해진 비트 수만큼 오른쪽 이동
다음 필터 기준값 = 현재 필터 기준값 + 기준 갱신량
```

갱신량이 양수면 파형이 상승하는 중이고, 음수면 하강하는 중이다. 갱신량의 절댓값이 기울기 기준을 넘을 때만 유효한 기울기로 인정하므로 작은 흔들림은 방향 판단에서 제외한다.

유효한 기울기가 생기면 그 부호를 “직전 유효 방향”으로 기억한다. 다음 유효 기울기의 부호가 이전 부호와 다를 때만 방향 전환 사건을 한 번 만든다. 유효 기울기가 없는 표본은 이전 부호를 바꾸지 않는다. 따라서 작은 잡음 사이에서도 마지막으로 확인한 실제 상승·하강 방향을 유지할 수 있다.

```text
유효 기울기 부호:  +  →  +  →  -
이전 부호와 비교:  없음   동일   다름
flip 사건 신호:     0      0      1

유효 기울기 부호:  +  →  +  →  +
flip 사건 신호:     0      0      0
```

새 60초 구간이 시작되면 필터 기준, 상승·하강 상태와 이전 유효 부호를 지운다. 60초 동안 유효 기울기 횟수와 방향 전환 횟수를 각각 세고, 방향 전환 사건은 Snapshot의 파형 형태 클래스 누적값에 전달한다. 이 기능을 RTL에서는 `dscr_spike_counter`가 담당한다.

### 5.3.2 한 박동의 최대 진폭을 코드로 남기기

30분 전체에서 최고점 하나만 찾으면 어느 박동의 값인지 알 수 없고 서로 다른 박동이 섞인다. 그래서 앞에서 예측한 다음 RR 시점 주변에만 짧은 관찰 구간을 연다. 예측 시점에 가까워지면 지금까지의 최대값과 “박동을 보았는가” 표시를 0으로 초기화한다. 현재 고정 설정에서는 별도 입력 정규화를 사용하지 않고 기준선을 숫자 0으로 두므로, 각 표본값에서 0을 뺀 뒤 음수는 0으로 잘라 양의 진폭만 본다.

진폭은 여러 단계의 문턱과 비교한다. 예를 들어 낮은 문턱부터 세 번째 문턱까지 넘었다면 진폭 코드 3이 된다. 새 코드가 지금까지의 최대 코드보다 클 때만 최대값을 교체한다. 관찰 구간 안에서 박동이 검출되면 박동 직후의 표본도 놓치지 않도록 일정 기간 관찰을 더 유지한다. 이 기간이 끝났고 실제 박동이 있었다면 최대 진폭 코드와 “코드가 유효하다”는 사건을 출력한다. 60초 동안 유효 코드의 횟수와 코드 합을 모아 Snapshot의 진폭 증거로 사용하고, 코드 합은 30분 Final Membrane에도 전달한다. 즉 박동 파형 전체를 저장하는 대신 박동 하나를 작은 최대 진폭 코드 하나로 압축한다. 이 기능을 RTL에서는 `ram_peak_accumulator`가 담당한다.

### 5.3.3 박동 전후에서 폭·복잡도·에너지 구하기

같은 RR 간격을 가진 박동이라도 QRS 주변 활동이 얼마나 오래 이어지는지, 방향이 몇 번 바뀌는지, 기준선에서 얼마나 크게 벗어나는지는 다를 수 있다. 이를 구하려면 박동이 검출된 한 시점만 보는 것이 아니라 앞뒤의 숫자를 함께 보아야 한다. 회로는 박동 전 120표본을 계속 보관하다가 박동이 검출되면 박동 후 100표본을 추가로 관찰한다.

- **박동 전 120표본:** 가장 오래된 표본은 버리고 새 표본을 넣는 방식으로 강한 사건, 방향 전환과 에너지 코드 이력을 유지한다. 동시에 강한 사건의 횟수, 방향 전환 횟수, 에너지 합과 첫·마지막 강한 사건 위치를 갱신한다.
- **박동 시작:** 박동이 검출되면 직전 120표본의 횟수와 합을 별도 상태에 복사하고 100표본의 박동 후 관찰을 시작한다. 박동 전에 강한 사건이 있었다면 가장 오래된 사건을 시작 위치, 가장 최근 사건을 마지막 위치로 잡는다.
- **박동 후 100표본:** 강한 사건 신호가 나타날 때 첫 위치와 마지막 위치를 갱신하고, DSCR 방향 전환을 세며, 매 표본값의 `abs(sample-baseline)>>ENERGY_SHIFT` 코드를 포화 누산값에 더한다.
- **폭(width):** 박동 전후를 하나의 시간축으로 놓고 첫 강한 사건 위치에서 마지막 강한 사건 위치를 뺀다. 사건이 없으면 폭은 0이다. 계산한 폭이 고정 기준보다 넓거나 최근 박동으로 만든 평균적 폭에서 크게 벗어나면 폭 이상 사건을 만든다.
- **복잡도(complexity):** 같은 220표본 안에서 앞의 DSCR 방향 전환이 몇 번 발생했는지 센다. 개별 방향 전환 사건을 박동 하나의 관찰 구간으로 다시 묶은 값이다.
- **에너지:** 각 표본값이 기준선에서 떨어진 거리를 절댓값으로 구하고, 비트 이동으로 작은 8비트 코드로 만든 뒤 220표본 동안 더한다. 합을 다시 작은 6비트 코드로 줄이고 최근 박동의 에너지 기준과 비교한다. 기준에서 크게 벗어나면 에너지 이상 사건을 만든다.
- **박동 전 활동도:** 박동 직전 120표본에 강한 사건이 있었는지, 방향 전환이 반복되었는지, 에너지 합이 충분히 컸는지를 함께 보고 박동 전 활동 사건을 만든다.

박동 후 100표본을 모두 본 뒤 폭·복잡도·에너지 값을 먼저 저장한다. 다음 클록에는 최근 기준과의 차이를 계산하고, 그 다음 클록에 유효 사건과 폭·복잡도·에너지·박동 전 활동 이상 사건을 출력한다. 폭과 에너지의 최근 기준도 이때 새 값 쪽으로 조금 이동한다. 이렇게 관찰, 비교, 출력 단계를 서로 다른 클록으로 나누어 긴 조합 경로를 피한다. 새 60초 구간이 시작되면 박동 전 이력, 진행 중인 관찰, 최근 기준과 출력 준비 상태를 모두 초기화한다. 출력 사건과 코드는 Snapshot의 파형 형태 점수와 60초 계수기에 들어가고, 관련 횟수와 코드 합은 Final Membrane의 장시간 집계로 전달된다. 이 기능을 RTL에서는 `qrs_maf_neuron`이 담당한다.

### 5.3.4 QRS 뒤쪽의 지연 활동 확인하기

이 경로는 앞의 박동 사건을 그대로 시작점으로 쓰지 않는다. 강한 변화나 유효 기울기 활동이 0에서 1로 바뀌는 순간을 별도의 QRS-like 시작점으로 잡는다. 시작 직후에는 같은 파형에서 다시 시작하지 않도록 짧은 불응기를 둔다. 이후 표본값이 들어올 때마다 시작점 이후 경과 표본 수를 1씩 올린다. 경과 80~160표본 사이에서는 10표본 간격의 위치 표시를 남기고, 90~170표본의 말단 구역에서는 활동이 나타난 표본 수를 센다. 활동이 일정 기간 사라지거나 최대 관찰 길이에 도달하면 한 박동의 관찰을 끝낸다.

활동이 나타난 가장 늦은 위치를 폭의 대리지표로 사용한다. 이 위치가 충분히 늦으면 넓은 파형 사건을 만들고, 말단 구역의 활동 횟수가 기준을 넘으면 말단 활동 사건을 만든다. 두 조건이 동시에 참일 때만 박동 단위의 RBBB-like 사건이 된다. 60초 동안 넓은 파형 횟수, 말단 활동 횟수와 두 조건의 결합 횟수를 따로 센다. 60초 경계에서는 결합 박동이 여러 번 반복되었는지와 리듬이 지나치게 불규칙하지 않은지를 함께 확인한 뒤 구간 단위 증거를 만든다. 이 증거는 Snapshot 클래스 점수와 Final Membrane의 장시간 집계에 전달된다. 따라서 한 박동의 늦은 활동만으로 클래스를 정하지 않는다. 이 기능을 RTL에서는 `rbbb_qrs_delay_bank`가 담당한다.

| 관찰 대상 | 필요한 이유 | 구체적인 하드웨어 처리 | 생성 상태 | 사용 위치 | 구현 모듈 |
|---|---|---|---|---|---|
| 기울기 방향 | 파형 굴곡과 방향 전환 | 필터 기준 오차, 유효 부호 유지, 부호 전환 검출 | 기울기/전환 스파이크 | Snapshot 파형 형태 횟수 | `dscr_spike_counter` |
| 최대 진폭 | 박동별 양의 최고점 압축 | 예측 박동 관찰 구간, 문턱 후보 코드, 최댓값 유지, 후속 유지 구간 | 최대 코드+유효 스파이크 | 코드 합/횟수 | `ram_peak_accumulator` |
| QRS 폭 | 활동 구간 길이 대리지표 | 박동 전·후 유한 구간의 첫/마지막 강한 사건 위치 | 폭 값/이상 스파이크 | 클래스 상태+Final 집계 | `qrs_maf_neuron` |
| QRS 복잡도 | 박동 구간 내 반복 굴곡 | DSCR 방향 전환 횟수를 6비트 포화 코드로 확정 | 복잡도 코드/스파이크 | 파형 형태 기여 | `qrs_maf_neuron` |
| QRS 에너지 | 기준 대비 박동 에너지 편차 | 표본별 절대 편차 코드 합, 적응 기준 | 에너지 코드/스파이크 | 파형 형태 기여 | `qrs_maf_neuron` |
| Pre-QRS 활동 | 주 사건 직전 작은 활동 | 120표본 강한 사건/방향 전환/에너지 이력 저장 | bump 스파이크 | Snapshot/Final 계수기 | `qrs_maf_neuron` |
| 말단 지연 | 넓고 늦은 활동의 반복 | 시작 나이, 말단 구역 활동도, 반복 박동 횟수, 리듬 조건 | 박동/구간 사건 | 클래스 점수 조건 | `rbbb_qrs_delay_bank` |

*표 9. 파형 형태·진폭 경로의 실제 유한 상태 기구.*

**통합 해석 경계.** DSCR, RAM, QRS MAF와 RBBB-like 경로는 파형을 압축한 공학적 대리지표다. 유도와 데이터베이스 스케일의 영향을 받을 수 있고, 표준 파형 형태 측정이나 임상 RBBB 검출기가 아니다. 현재 원천에서 안전하게 확인되지 않는 parameterized aggregate 상태 총량은 `UNRESOLVED_FROM_STATIC_AUDIT`로 유지한다.

## 5.4 60초 Snapshot과 30분 Final Membrane

개별 사건 하나는 클래스를 결정하기에 충분하지 않다. RR 불일치 하나는 일시적 잡음일 수 있고, 높은 최대 코드 하나는 유도 스케일의 영향일 수 있으며, 기울기 방향 전환 하나는 정상 QRS 굴곡에서도 발생할 수 있다. 따라서 사건 신호를 바로 label로 바꾸지 않고 60초와 30분 두 단계에서 결합한다.

여기서 30분은 생리학적으로 최적이라고 새로 가정한 시간이 아니다. 24시간 Holter형 장기 관찰을 최종 지향점으로 두되, 현재 네 공개 원천에 공통으로 적용할 수 있는 실제 record 길이가 30분이므로 Final Membrane 깊이를 Snapshot 30개로 고정한 것이다 [CLM-035]. 이 선택은 클래스별 입력 길이를 같게 만들어 평가 조건을 통제하지만, 24시간 동안 드물게 나타나는 사건을 검증하지는 못한다.

### 5.4.1 60초 Snapshot 누적

`class_score_neurons`는 PNN 일치/불일치, RDM 코드, DSCR 기울기/전환, RAM 코드, ectopic pair, QRS MAF 이상 사건, pre-QRS bump와 RBBB-like 구간 사건을 입력으로 받는다. 각 사건에는 네 클래스에 대한 고정된 부호 기여값이 있다. 양의 기여는 해당 클래스 상태를 올리는 흥분, 음의 기여는 내리는 억제다. 리듬과 파형 형태의 국소 상태는 분리되어 갱신되다가 판독에서 더해진다. 동시에 박동 수, 사건 수, 코드 합과 일정 비율·평균 조건을 60초 계수기로 유지한다.

60,000번째 수락 표본에서 최상위 FSM이 `segment_done`을 만들면 계수기의 이전 값만 읽어 마지막 사건을 놓치지 않도록 `*_count_next`를 Snapshot 레지스터에 확정한다. 클래스 판독 파이프라인은 사건 단위 변화량, 60초 단위 비율·평균 변화량과 구조 조건을 순서대로 막전위에 반영한다. 이어서 네 64비트 Snapshot 클래스 상태를 엄격한 WTA로 비교해 국소 `pred_class/pred_valid`를 만든다. 다음 `segment_start`에서 국소 이력·계수기·적응 기준을 초기화한다. 반면 이미 확정된 Snapshot 승자와 집계 특징은 `final_membrane_layer`가 받아 30분 상태에 더한다.

### 5.4.2 60초 승자의 의미

Snapshot 예측은 “이 60초에서 어느 클래스 누적값이 가장 컸는가”라는 중간 결론이다. 30분 전체의 정답이 아니므로 한 Snapshot이 불규칙해 보여도 나머지 29개가 다른 클래스를 계속 지지하면 최종 판정은 달라질 수 있다.

### 5.4.3 30분 Final Membrane 누적

60초 Snapshot 하나가 끝날 때마다 Final Membrane에는 다음 정보가 더해진다.

- 네 Snapshot 승자 횟수
- 박동, PNN 불일치, ectopic-pair, QRS MAF, RBBB-like와 pre-QRS 횟수
- 이상·리듬·파형 형태 집계값
- RDM 유효 횟수와 코드 합, RAM 코드 합

30번째 Snapshot에서는 마지막 60초의 값까지 빠뜨리지 않고 30분 집계 레지스터에 먼저 저장한다. 그 뒤의 판정 단계는 이렇게 완전히 고정된 30분 값만 사용한다. 네 클래스의 기본 누적값은 각 클래스가 60초 승자가 된 횟수에서 시작한다. 여기에 박동·리듬·파형 형태가 30분 동안 얼마나 반복되었는지를 더하거나 뺀다. 따라서 Final Membrane은 단순 다수결보다 더 많은 장시간 정보를 사용한다.

### 5.4.4 장시간 보정과 최종 선택

단순히 60초 승자 횟수만 비교하면 짧은 잡음 구간이나 약하게 반복되는 특징을 놓칠 수 있다. 이를 줄이기 위해 다음 순서로 네 클래스 누적값을 보정한다.

1. **기본값:** 60초 승자 횟수로 네 클래스의 시작 누적값을 만든다.
2. **충돌 억제(guard):** 승자 횟수는 한 클래스를 가리키지만 30분 리듬·파형 정보가 강하게 반대하면 과도한 보정을 막는다.
3. **구조 보강(rescue):** 60초 승자 횟수에서는 밀렸더라도 한 클래스를 지지하는 특징이 여러 구간에서 지속되면 그 클래스 누적값을 보강한다.
4. **반대 증거 억제(veto):** 특정 클래스와 모순되는 증거가 충분하면 그 클래스 누적값을 낮춘다.
5. **조용한 AFF 보정(silent-AFF):** AFF가 60초 승자로 자주 나타나지 않더라도 장시간 집계가 특정 AFF 형태를 계속 지지하면 AFF를 보강하고 경쟁 CHF를 낮춘다.

이 보정은 임상 진단 규칙이 아니라 고정 classifier가 60초 다수결의 실패를 줄이기 위해 사용하는 정수 누적 규칙이다. 실제 문턱값과 가중치는 고정 설정 파일을 따르며 본문에서 새 숫자를 만들지 않는다.

**설명용 장시간 예.** 30개 중 한 60초 구간에서 잡음 때문에 불규칙 사건이 많아 ARR 국소 승자가 되었더라도, 나머지 구간의 승자와 리듬·파형 형태 집계값이 일관되게 다른 상태를 지지하면 그 한 구간이 최종 판정을 자동 지배하지 않는다. 반대로 약한 국소 증거가 여러 구간에 반복되면 승자 횟수와 집계 상태 양쪽에 누적되어 장시간 지속성이 된다. 이 예 역시 상태 동작 설명이며 임상 사례가 아니다.

**가장 큰 누적값 선택.** 모든 보정이 끝나면 NSR 누적값을 첫 후보로 두고 CHF, ARR, AFF를 차례로 비교한다. 새 값이 현재 후보보다 **클 때만** 후보를 바꾼다. 값이 같으면 먼저 있던 후보를 유지하므로 동률 우선순위는 NSR→CHF→ARR→AFF로 항상 같다. 가장 큰 클래스 번호가 `final_pred`, 비교 직전 네 누적값이 `final_mem`이다. 보드 검증에서 클래스 번호뿐 아니라 네 누적값까지 비교한 이유는 승자만 우연히 같고 내부 계산이 다른 오류까지 찾기 위해서다.

```text
60초 Snapshot이 끝날 때마다:
    해당 60초의 승자 횟수를 1 올린다.
    박동·리듬·파형 형태의 횟수와 코드 합을 30분 합계에 더한다.

30번째 Snapshot이 끝나면:
    승자 횟수로 네 클래스의 기본 누적값을 만든다.
    30분 특징 합으로 충돌 억제·구조 보강·반대 증거 억제를 적용한다.
    네 누적값을 차례로 비교해 가장 큰 클래스를 출력한다.
```

[근거: CLM-003; Snapshot 점수·Final Membrane RTL; digital commit `c6b80de...`]

## 5.5 Streaming state와 하드웨어 구현 방식

최상위 제어기는 다음 순서로 동작한다. 시작 명령을 기다리고, 내부 상태를 지운 뒤, 새 60초 구간을 연다. 그다음 입력과 준비 신호가 모두 참일 때만 표본값을 하나씩 받는다. 60,000번째 표본값을 받으면 입력을 잠시 멈추고, 아직 파이프라인에 남아 있는 사건과 점수가 모두 계수기에 반영될 때까지 기다린다. 계산이 끝나면 60초 Snapshot을 Final Membrane에 전달하고 다음 구간을 시작한다. 이 과정을 30번 반복한 뒤에만 최종 출력이 유효하다는 신호를 낸다. RTL에서는 이 순서를 `IDLE→CORE_RESET→SEG_START→RUN→SEG_DONE→FLUSH→COMMIT→DONE` 상태로 구현하며, 최상위 모듈은 `snn_ecg_30min_final_top`이다.

RTL에 적합한 특성은 다음과 같다.

- 표본값마다 부호 있는 뺄셈, 비트 이동, 비교와 작은 누산기만 갱신한다.
- 박동 중심 이력은 QRS MAF의 박동 전 120표본과 박동 후 100표본처럼 길이가 정해져 있다.
- 60초 계수기는 구간 시작에서 초기화되고 Final Membrane만 30개 Snapshot에 걸쳐 지속된다.
- 부동소수점 추론, 행렬 곱셈기, 추론 중 학습 메모리가 없다.
- Pure RTL은 전체 30분 원시 파형을 저장하지 않는다 [CLM-023].

```text
1,800,000 samples × 12 bits
= 21,600,000 bits
= 2,700,000 bytes
≈ 2.7 MB (decimal)
```

이 값은 전체 원시 입력 구간 저장을 피한 양, 즉 **avoided full raw-input window storage**다. 실제 합성 레지스터 총량, MicroBlaze 메모리, 측정된 메모리 절감량, 전력 또는 속도 증거가 아니다. 일부 파라미터형 상태 묶음은 정적 감사만으로 정확한 전체 비트 수를 안전하게 합산하지 않았으므로 절감률도 계산하지 않는다.

| 시간 유지 범위 | 대표 상태 | 갱신/확정 시점 | 초기화 범위 |
|---|---|---|---|
| 표본값 사이 | 직전 표본값, 필터, QRS 막전위, 불응기 | 수락 표본값 | 코어/60초 구간별 규칙 |
| 박동 사이 | 직전 박동 이후 표본 수, RR 예측값, 직전 RR, 적응 RR 기준 | 박동 또는 새 표본 | 60초 구간 시작 |
| 박동 관찰 구간 | 최대 진폭 코드, 박동 전후 상태, 시작점 이후 표본 수 | 표본/박동/관찰 종료 | 박동/60초 구간 |
| 60초 | 사건/코드 계수기, Snapshot 클래스 막전위 | 사건과 `segment_done` | 다음 60초 구간 시작 |
| 30분 | 승자 횟수, 집계 합, Final Membrane | Snapshot/30분 종료 | 첫 60초 구간의 초기화 신호 |

*표 10. 지속 상태의 시간 범위. [근거: CLM-023; `tables/streaming_state_inventory.csv`; `docs/STREAMING_STATE_MEMORY_KR.md`]*

표 10은 상태가 없다는 뜻이 아니라 상태 크기가 1,800,000표본 원시 배열로 증가하지 않는다는 뜻이다. 이 상태 계층이 표본값→박동→Snapshot→Final로 정보를 옮기는 핵심 하드웨어 아키텍처다.

## 5.6 RTL/IP/FPGA 구현

디지털 구현은 Python 고정 기준 모델→전체 최상위 RTL/XSim→Vivado 구현→AXI/IP-XACT package→Vitis/MicroBlaze 재생→Nexys A7 FPGA 순서로 진행하였다. Pure RTL 범위는 가속기 코어만 포함한다. MicroBlaze 전체 system 범위는 processor, local memory, UART, 표본값 공급기와 코어를 모두 포함하므로 두 결과는 같은 면적 범위가 아니다.

| 구현 범위 | LUT | FF/register | BRAM | DSP | timing 결과 |
|---|---:|---:|---:|---:|---:|
| Pure RTL 가속기 | 9,719 | 5,038 | 0 | 0 | WNS 8.184 ns |
| MicroBlaze 전체 재생 system | 12,494 | 8,494 | 16 | 3 | setup WNS 0.097 ns |

*표 11. FPGA 자원과 timing closure. [근거: CLM-008, CLM-009, CLM-010; 고정 Vivado 결과]*

실제 Vivado Device View에 routed checkpoint의 계층별 배치 좌표를 정합한 주석 Figure와 Vivado native Block Design·timing schematic은 부록 D에 제시한다.

Pure RTL의 0 BRAM/0 DSP는 고정 폭 streaming datapath와 일관된다. 그러나 BRAM 0 하나만으로 전체 관찰 구간을 저장하지 않는다는 사실을 증명하지는 못한다. 그 근거는 RTL에서 확인한 직전 표본, 계수기, 유한 박동 구간과 장시간 누적 상태다. MicroBlaze의 BRAM/DSP에는 software와 재생 기반 구조가 포함되므로 pure core와 단순 감소율을 계산할 수 없다. WNS는 구현 제약의 timing slack이며 한 30분 판정의 처리 지연시간이 아니다.

AXI wrapper는 시작 신호, valid/ready, 최종 클래스와 네 막전위를 연결하고 IP-XACT `component.xml`로 묶는다. MicroBlaze application은 고정 `.mem`을 표본값 공급기로 전달한다. 코어가 표본값 1,800,000개와 Snapshot 30개를 처리하면 최종 출력을 UART로 반환한다. 이는 디지털 IP가 보드 system 안에서 동작했다는 증거이지 live 전극 획득이나 fabricated SoC 증거가 아니다.

# 6. 가속기 Benchmark와 아날로그·디지털 통합 검증

디지털 IP 구현 뒤에는 두 질문을 분리해 확인한다. 첫째, 동일한 30분 분류 작업에서 가속기 코어가 저장 데이터를 얼마나 빨리 처리하는가. 둘째, AFE XMODEL이 만든 signed stream이 디지털 RTL과 FPGA 경계까지 변형 없이 전달되고 같은 내부 상태와 판정을 만드는가. 첫 질문은 완료된 NO_BOARD benchmark의 measured CPU와 cycle-derived core 결과로, 두 번째 질문은 SHA256과 bit-exact 비교로 검증하였다.

## 6.1 가속기 Benchmark 결과와 해석 범위

Benchmark는 고정 분류기와 RTL을 바꾸지 않고 digital 저장소 `main`의 `09e4d840...`에서 수행했다. 36개 입력은 각각 1,800,000개 표본이며 Exact C++ 측정 전에 최종 예측 36/36, 네 막전위 144/144와 Snapshot 경계 1,080/1,080 일치를 확인하였다. 즉 CPU 기준선이 다른 계산을 빠르게 수행한 것이 아니라 고정 RTL과 같은 결과를 만드는지 먼저 통과시켰다 [CLM-018, CLM-047].

대표 CPU 기준선은 hand-written single-thread transaction-level Exact C++다. 36 cases를 각 10회 측정한 360-run kernel 중앙값은 1,777.699800 ms이고, 파일 open·입력 해석·결과 JSON 기록을 포함한 end-to-end 중앙값은 2,007.549250 ms다. Python 주기 모델은 검증용이라 대표 CPU speedup 계산에 사용하지 않았고, Verilator host runtime도 RTL simulation 시간이므로 CPU inference 기준선으로 사용하지 않았다 [CLM-043].

Pure RTL은 canonical `sample_gap_cycles=2`, profile total 5,401,260 cycles와 구현 clock 100 MHz를 사용한다. 따라서 저장된 30분 ECG의 accelerator-core 처리시간은 `5,401,260 / 100,000,000 = 54.012600 ms`이고 처리량은 33,325,557.369947 samples/s, 즉 33.325557 MSamples/s다. 1 kSPS 입력률보다 계산 처리량이 33,325.56배 높다는 뜻이다 [CLM-044].

같은 저장 데이터 kernel 범위에서 처리시간 비율은 다음과 같다.

```text
Exact C++ 1,777.699800 ms / FPGA core 54.012600 ms = 32.912687×
```

이 값은 **단일 스레드 Exact C++ 대 cycle-derived FPGA-core speedup estimate**다. CPU 시간은 측정값이지만 FPGA core 시간은 cycle에서 산출했으므로, 측정 보드 speedup이나 MicroBlaze 전체 system speedup으로 표현하지 않는다. host 전송, MicroBlaze, UART와 board software overhead도 포함하지 않는다 [CLM-045].

| 구현·범위 | 처리시간 | 처리량 | 상태와 해석 |
|---|---:|---:|---|
| Exact C++ kernel | 1,777.699800 ms | 1,012,544.413 samples/s | measured, single thread, 입력 적재 후 결과까지 |
| Exact C++ end-to-end | 2,007.549250 ms | 896,615.633 samples/s | measured, 파일 입력과 결과 기록 포함 |
| Pure RTL FPGA core | 54.012600 ms | 33,325,557.369947 samples/s | cycle-derived, 저장 데이터 accelerator-core 범위 |
| 기존 FPGA replay | 미측정 | 미측정 | pred/mem 36/36 기능 검증만 완료 |
| 물리 board timing·power | `PENDING_BOARD` | `PENDING_BOARD` | timer 실행과 실측 전력 필요 |

*표 12. 저장된 30분 ECG의 CPU와 FPGA-core 처리 비교. 동일 분류 입력을 사용하지만 measured CPU와 cycle-derived core를 결합한 비교이며 물리 board speedup이 아니다. [직접 근거: `benchmarks/accelerator_benefit/results/cpu_fpga_comparison.csv`; `benchmarks/accelerator_benefit/results/rtl_cycle_summary.json`; CLM-043~CLM-045]*

`54.012600 ms`는 이미 저장된 표본을 처리하는 active compute time이다. 실제 ECG가 1 kSPS로 들어오면 1,800,000개 표본을 모으는 데 30분이 걸리므로 live 환경의 최종 판정시간이 54 ms가 되는 것은 아니다. 이 처리 여유는 입력이 들어오는 동안 표본별 상태를 갱신하고 다른 시스템 작업과 전력 절감을 설계할 가능성을 보여주는 값이다.

Vivado 추정 전력 0.099 W에 cycle-derived 처리시간을 곱하면 0.005347247400 J/decision이다. 두 값은 모두 추정 범위이며 물리 보드에서 측정한 전력·에너지가 아니다. 물리 board timing, power와 energy는 계속 `PENDING_BOARD`다 [CLM-046].

## 6.2 AFE·디지털 통합 XMODEL 검증

End-to-end 검증은 같은 “36/36” 표기 안의 서로 다른 질문을 분리한다.

1. **입력 SHA256 36/36:** XMODEL AFE에서 만든 최종 시험 구간과 보드 재생용 `.mem`의 byte가 같은가?
2. **Canonical AFE→RTL pred/mem 36/36:** 같은 byte와 `sample_gap_cycles=2`에서 고정 RTL이 기준 클래스와 네 막전위를 재현하는가?
3. **XSim→FPGA pred/mem 36/36:** package된 보드 system이 XSim 상태를 재현하는가?
4. **정답 표지 29/36:** 재현한 출력 클래스가 공개 데이터셋 정답과 같은가?

![그림 15. 기능 등가성](../figures/final/FIG-08_signed_stream_handoff.svg)

*그림 15. 입력 byte 동일성, 기준 RTL 상태 동일성과 정답 표지 일치의 분리. [직접 근거: `components/afe_xmodel/docs/integration_latest/afe36_sha256_bitidentity.csv`; `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv`; `components/digital_accelerator/reports/final/board_replay_36_batch_summary.json`]*

| 비교 경계 | 결과 | 증명하는 것 | 증명하지 않는 것 |
|---|---:|---|---|
| AFE 구간↔보드 입력 | SHA256 36/36 | 입력 byte 동일성 | 실제 아날로그 정확도 |
| AFE 구간↔고정 RTL | pred/mem 36/36 | canonical 상태 재현 | 정답 표지 100% 일치 |
| XSim↔FPGA | pred/mem 36/36 | package된 디지털 기능 등가성 | 임상 유효성 |
| FPGA 출력↔정답 표지 | 29/36 | 현재 데이터셋 분류 결과 | 다른 환경으로의 일반화 |

*표 13. End-to-end 기능 등가성과 분류 정확도의 경계. [근거: CLM-011~CLM-013, CLM-021]*

예측과 네 막전위를 함께 비교하는 이유는 클래스 승자만 우연히 같고 내부 점수가 다른 오류까지 찾기 위해서다. 따라서 FPGA 36/36은 같은 입력에 대해 내부 상태까지 재현했음을 지지하지만 classifier의 정답 표지 정확도를 100%로 만들지는 않는다. 실제 AFE PCB, ADC silicon, transistor/post-layout, live electrode와 clinical 검증은 수행하지 않았다 [CLM-020].

XMODEL/emulator로 만든 full-record signed stream은 `start=2000+chunk_id×1,800,000` 규칙으로 최종 시험 36개 구간을 자른다. 이 36개가 board-replay 입력과 SHA256 36/36 동일했고, canonical `sample_gap_cycles=2`에서 locked full-top RTL의 `final_pred`와 네 `final_mem`도 각각 36/36 bit-exact였다 [CLM-012, CLM-013]. 이는 MATLAB 공칭 벡터 하나가 곧 장시간 분류 정확도를 증명한다는 뜻이 아니라, 파라미터 정의→XMODEL stream→RTL 입력 사이의 형식과 byte 경계가 추적된다는 뜻이다.

# 7. 실험 결과

앞 절까지의 설계와 검증 절차를 바탕으로 분류 성능, mixed-signal 인계와 디지털 구현 결과를 구분해 제시한다. 기능 등가성 36/36은 같은 입력에 대한 구현 일치를 뜻하며 정답 표지 정확도와 동일한 지표가 아니다.

## 7.1 분류 성능

학습 결과 61/68=89.71%는 고정 특징과 가중치가 학습 자료의 패턴을 어느 정도 표현하는지 확인한 값이다. 검증 결과 32/32=100.00%는 Final Membrane 모델 선택에 사용했으므로 새로운 자료에 대한 최종 일반화 성능으로 승격하지 않는다 [CLM-006]. 모델을 고정한 뒤 한 번만 평가한 최종 시험 30분 구간은 29/36=80.56%, macro F1 80.44%, balanced accuracy 80.56%였다 [CLM-004]. 이 값이 본 보고서의 주 분류 결과다. 같은 최종 partition을 원본 record별 다수결로 합치면 16/19=84.21%, macro F1 80.80%, balanced accuracy 88.19%였다 [CLM-005]. Record-majority는 여러 30분 구간의 흔들림이 원본 record 단위에서 얼마나 완화되는지를 보여주지만 별도의 독립 시험은 아니다.

![그림 16. 분류 결과](../figures/final/FIG-10_classification_summary.svg)

*그림 16. 검증 결과는 모델 선택용으로 분리하고 고정 최종 시험 결과를 중심에 둔 분류 요약.*

| 평가 구간 | 정답/전체 | 정확도 | Macro F1 | 해석 |
|---|---:|---:|---:|---|
| 학습 | 61/68 | 89.71% | — | 모델 적합 확인 |
| 검증 | 32/32 | 100.00% | — | 모델 선택 전용 |
| 고정 최종 30분 구간 | 29/36 | 80.56% | 80.44% | 주 held-out 결과 |
| 최종 record-majority | 16/19 | 84.21% | 80.80% | 같은 partition의 집계 |

*표 14. 분류 결과. [근거: CLM-004~CLM-007; 고정 최종 metrics]*

Record-majority의 상승은 일부 원본 record에서 30분 구간의 오류가 다수결로 완화되었음을 보이지만 독립 시험 재현은 아니다. 클래스별 최종 구간의 혼동 행렬은 표 15와 같다.

| 정답\예측 | NSR | CHF | ARR | AFF | 재현율 |
|---|---:|---:|---:|---:|---:|
| NSR | 9 | 0 | 0 | 0 | 100.00% |
| CHF | 0 | 6 | 0 | 3 | 66.67% |
| ARR | 2 | 0 | 7 | 0 | 77.78% |
| AFF | 1 | 0 | 1 | 7 | 77.78% |

*표 15. 고정 최종 시험 30분 구간의 혼동 행렬. 행은 정답, 열은 예측이다. [근거: CLM-004]*

CHF 3건이 AFF로, ARR 2건이 NSR로, AFF 각 1건이 NSR과 ARR로 분류되었다. CHF 재현율 66.67%가 가장 낮고 클래스당 시험 구간이 9개뿐이므로 전체 정확도 하나만으로 모든 클래스가 균일하게 분류된다고 주장하지 않는다.

## 7.2 Mixed-signal 및 디지털 통합 결과

MATLAB 공칭 검증은 선택한 입력이 ADC 상·하한 안에 있음을 보였다. XMODEL의 RMS와 지연 결과는 연속시간 solver 모델과 디지털 emulator가 안정화 이후 유사한 파형을 냈음을 보였다. SHA256 36/36은 그 결과로 만든 디지털 byte가 보드 입력까지 바뀌지 않았음을 보였고, canonical AFE→RTL 36/36은 동일 byte에서 클래스와 네 막전위 상태가 보존되었음을 보였다.

이 네 결과는 차례로 공칭 입력 범위, 모델 간 정합, 입력 무결성과 디지털 상태 재현을 답한다. 어느 하나도 실제 전극에서 silicon까지의 정확도나 임상 효능을 직접 증명하지 않는다. 반대로 모델 기반 아날로그 한계가 남더라도 이미 고정한 byte에 대한 RTL 상태 재현 결과는 유효하다.

## 7.3 하드웨어 구현 결과

Pure RTL 구현에서 양의 WNS와 0 BRAM/0 DSP를 확인했고, 묶음화한 MicroBlaze system도 양의 setup WNS를 보였다. 보드 36개 사례 모두 수락 표본값 1,800,000개, Snapshot 30개와 한 번의 판정을 완료했다. `final_pred`와 `final_mem`은 각각 36/36 예상 출력과 일치했으므로 FPGA 묶음화 과정에서도 고정 RTL의 상태 전이가 보존되었다. 그러나 같은 출력의 정답 표지 비교는 29/36이므로 기능 등가성과 분류 정확도는 서로 다른 결과다.

# 8. 종합 논의와 한계

이 장에서는 앞의 수치를 다시 나열하기보다 설계가 기존 접근과 달라지는 지점, 결과가 지지하는 범위와 아직 확인하지 못한 범위를 해석한다.

## 8.1 설계적 차별성과 기술적 의의

본 설계의 차별성은 “ECG를 FPGA에서 빠르게 계산했다”거나 “60초와 30분을 사용했다”는 문장보다 입력 신호를 시간 계층과 상태 전이로 재구성한 데 있다. 인접 표본값은 사건 신호가 되고, 사건의 반복은 박동이 되며, 박동 사이 시간은 리듬 상태가 된다. 박동 중심의 유한 관찰 구간은 최대 진폭·폭·복잡도·에너지·말단 활동도로 압축된다. 제한 길이 Snapshot은 대부분 정상인 기록 속에서 질환성이 강한 국소 구간을 포착하고, 기록 상태는 Snapshot별 증거 강도, 승자 빈도, 반복 사건과 장시간 일관성을 누적한다. 현재 구현에서는 이 계층을 60초 Snapshot과 30분 Final Membrane으로 검증하였다. 따라서 한 입력 표본값이 최종 클래스에 영향을 주는 경로를 직전 표본 레지스터, 사건 펄스, 계수기, Snapshot과 Final 상태 순서로 추적할 수 있다 [CLM-042].

SNN-inspired 구조의 의미도 여기서 분명해진다. 모든 파형값을 밀집 벡터로 보존하는 대신 의미 있는 변화가 일어날 때 사건을 만들고, 막전위형 누산값과 문턱값으로 시간 증거를 판정에 반영한다. QRS 검출기의 일반 구조는 누설을 지원하지만 현재 고정 설정의 누설값은 0이다. Final Membrane은 양·음의 클래스 상태와 승자독식을 사용한다. 이는 생물학적 뉴런의 충실한 모사가 아니라 사건 신호와 지속 상태를 이용한 하드웨어 추상화다.

하드웨어 기술성은 고정 폭 연산뿐 아니라 표본 수락과 상태 확정의 클록 순서에 있다. 사건 인코더의 직전 표본 갱신, QRS의 이전→다음 막전위, PNN 순차 탐색, QRS MAF의 다중 클록 평가, 60초 계수기의 `*_next` 저장과 Final `BASE→STRUCT→WTA`가 모두 정확한 순서를 요구한다. XSim, Vivado, IP-XACT와 보드 막전위 36/36은 이 순서가 package된 system에서도 보존되었음을 보여준다.

재현성은 재실행 여부만이 아니라 어떤 원천과 claim을 사용했는지까지 포함한다. 고정 component commit, 데이터셋 DOI/hash, 산출물 manifest, 담당자 표와 SAFE/CAREFUL/FORBIDDEN registry가 보고서 문장의 범위를 고정한다. 긴 경로와 hash는 부록 B/C로 이동하여 본문은 공학적 논리에 집중시켰다.

## 8.2 결과의 해석 범위와 향후 과제

가장 큰 과학적 한계는 클래스와 원천 데이터베이스가 결합된 database–class confounding이다. 원천 record 단위 분할은 직접 누출을 막지만 획득 장비, 유도, 대상군의 특징을 제거하지 않는다. 최종 시험은 36개 구간·19개 record이고 AFF는 한 record뿐이므로 구간 수의 균형이 대상자 다양성을 뜻하지 않는다. 다음 우선순위는 같은 획득 장비·유도·protocol에서 수집한 고정 다중 클래스 외부 시험이다.

관찰 시간도 제한된다. 구조의 동기는 24시간 Holter이지만 현재 학습·최종 시험·보드 재생은 모두 30분 창이다. 60초 Snapshot을 더 많이 누적하도록 계수 범위를 확장하는 것만으로 24시간 성능이 자동으로 보장되지는 않는다. 장시간에 맞춰 Final Membrane의 누적 폭, 문턱값, 간헐 사건의 희석과 시간대 변화 영향을 다시 고정하고, 동일 획득 조건의 24시간 다중 클래스 자료에서 재검증해야 한다 [CLM-035].

구조 차원에서는 Snapshot 단독, guard 없는 투표, 기본 막전위와 전체 구조 보정을 같은 untouched cohort에서 비교한 보고서용 ablation이 없다. 그러므로 Final Membrane이 정확도를 얼마나 높였는지 수치로 주장하지 않는다. 고정 변형 구조와 같은 분할·표본 입력 간격을 사용한 ablation이 필요하다.

아날로그·물리 검증 범위는 MATLAB/XMODEL까지다. PCB 기생성분, 전극 임피던스, ADC INL/DNL, post-layout와 fabricated silicon은 포함하지 않는다. 실제 AFE/ADC 코드를 같은 부호 인터페이스로 획득해 기준 벡터 및 XMODEL과 비교한 뒤, standard-cell 합성·배치배선·STA·측정으로 확장해야 한다.

| 한계 | 영향 | 현재도 유효한 증거 | 다음 검증 |
|---|---|---|---|
| DB–클래스 confounding | 생리 특징과 획득 환경 분리 불가 | 고정 분류·RTL 등가성 | 동일 획득/교차 영역 cohort |
| 30분 공통 평가 창 | 24시간의 희귀·간헐 사건 검증 불가 | 동일 길이 네 클래스 비교 | 24시간 동일 획득 다중 클래스 검증 |
| 제한된 record 수 | 클래스 불확실성 | 36개 구간 1회 시험 | 더 큰 독립 record 집합 |
| Ablation 부재 | 시간 계층 기여량 미확정 | 고정 전체 구조 | Snapshot/기본/전체 고정 변형 |
| 실제 AFE/ADC 부재 | 실제 강건성 미확정 | MATLAB/XMODEL 인계 | PCB/ADC 코드 측정 |
| ASIC/post-layout 부재 | 면적·전력 sign-off 없음 | FPGA 구현 가능성 | 배치배선·추출 STA·silicon |
| 임상 검증 부재 | 진단 claim 불가 | 공학 결과 | 승인된 전향 연구 protocol |
| Physical board benchmark 미완료 | system latency·실측 전력 미확정 | Exact C++ 대 cycle-derived core 비교 | timer 실행·idle/active 전력 측정 |

*표 16. 한계, 영향, 남는 증거와 구체적인 다음 검증. [근거: CLM-017~CLM-020, CLM-022]*

이 한계는 일반화와 물리·상용 claim을 제한하지만 같은 byte에서 확인한 RTL/IP/FPGA 기능 등가성을 소급해 무효화하지 않는다. 본 prototype은 임상 검증된 진단 장치, fabricated silicon 또는 상용 wearable보다 우수한 제품이 아니다.

# 9. 결론

아날로그 입력에서 디지털 분류기까지의 경계를 먼저 고정하였다. ECG의 느린 기준선 변동은 10 MΩ·33 nF 고역통과필터로 줄이고, 100 kΩ·1 kΩ 저항을 사용한 3-op-amp IA에서 차동 신호를 201배 증폭한다. 60 Hz 전원선 간섭은 26.526 kΩ·100 nF 중심의 active Twin-T와 독립 buffer로 억제하고, 1 kΩ·1.06 µF 저역통과필터가 150.15 Hz보다 높은 성분을 제한한다. ±1.65 V, 12-bit, 1 kSPS ADC는 이 파형을 offset-binary 코드로 바꾼 뒤 signed two's-complement stream으로 변환하여 RTL에 전달한다. 수동 notch의 넓은 저지대역과 출력 loading, IA 수렴, LPF 차단주파수, CMRR margin과 ADC 기록 시점 문제는 설계 과정에서 실제로 수정한 항목이다 [CLM-028~CLM-030].

MATLAB은 이 공칭 회로의 이득·주파수응답·동적 범위·ADC 코드 분포를 확인하고 같은 입력을 반복할 수 있는 기준 벡터를 만든다. XMODEL은 여기서 끝내지 않고 50/60 Hz 간섭, R/C mismatch, op-amp GBW와 VOS, ADC 비이상성 및 장시간 stream을 SystemVerilog 환경에서 가한다. 두 환경의 역할을 분리했기 때문에 MATLAB의 공칭 설계 의도, XMODEL의 비이상성 검증, SHA256으로 고정된 signed stream, RTL의 상태 전이를 한 방향으로 추적할 수 있다. 이는 실제 PCB, fabricated ADC, post-layout 또는 실제 전극 측정을 대신하는 결과가 아니라, 그 전 단계의 model-based mixed-signal handoff를 검증한 결과다 [CLM-001, CLM-002, CLM-015, CLM-031~CLM-034].

본 연구는 장시간 ECG를 순차 Snapshot으로 압축하고 간헐적인 질환성 구간의 증거를 기록 단위 상태로 연결하는 다중 시간축 SNN-inspired RTL 구조를 제안하였다. 현재 1 kSPS·60초 Snapshot·30분 Final Membrane은 공개 데이터에 맞춘 검증 사례다. 인접 표본값의 부호 있는 차이와 적응형 사건 문턱 bank가 파형 변화 펄스를 만들고, QRS 막전위·문턱값·불응기가 여러 펄스를 한 박동으로 묶는다. PNN은 반복 RR 가설과 다음 간격의 일치 여부를 보고, RDM은 연속 RR 절대 차이를 수준 코드로 바꾸며, ectopic 경로는 적응 기준에 대한 early–late 교대를 검출한다 [CLM-035, CLM-042].

파형 경로는 필터 기울기 부호를 보존해 DSCR 방향 전환을 검출하고, 예측 박동 관찰 구간에서 RAM 최대 진폭 코드를 남긴다. QRS MAF는 박동 전 120표본과 후 100표본의 강한 사건 위치, 기울기 방향 전환, 기준선 편차 에너지와 pre-QRS 활동도를 파이프라인으로 확정한다. RBBB-like 경로는 독립 활동 시작, 말단 관찰 구간과 반복되는 넓은 파형·지연 패턴을 구간 증거로 만든다. 이 사건과 코드는 고정 부호 기여값으로 Snapshot 클래스 상태를 갱신하고, 30개 승자 횟수와 집계값은 Final의 기본 막전위·guard·rescue·veto·silent-AFF 보정을 거쳐 결정적 WTA 출력이 된다.

엄격한 원천 record 단위 분할의 고정 최종 결과는 30분 구간 29/36=80.56%, record-majority 16/19=84.21%였다. Pure RTL은 9,719 LUT, 5,038 FF, 0 BRAM, 0 DSP와 양의 WNS를 보였다. AFE 입력 SHA, canonical AFE→RTL과 FPGA pred/mem은 각 경계에서 36/36 일치하였다. 전체 1,800,000표본 원시 관찰 구간을 저장하지 않지만 2.7 MB는 회피한 원시 입력 구간일 뿐 측정 절감량이 아니다.

따라서 주 기여는 최고 속도 경쟁이 아니라, 장시간 ECG 증거가 실제 레지스터·계수기·관찰 구간·FSM을 거쳐 최종 클래스가 되는 과정을 설명 가능하고 재현 가능한 반도체 IP로 완성한 데 있다. 저장 데이터 처리에서 Exact C++와 cycle-derived core의 처리시간 비율은 32.912687배였지만, 이는 보조 구현 결과이며 물리 보드 speedup이나 live 54 ms 진단을 뜻하지 않는다. 데이터베이스 결합, 실제·임상·ASIC 검증 공백, ablation과 physical board timing·power 측정을 다음 검증 과제로 남긴다 [CLM-043~CLM-046].

# 참고문헌

[1] U.S. Food and Drug Administration, “De Novo Classification Request for ECG App (DEN180044),” 2018. https://www.accessdata.fda.gov/cdrh_docs/reviews/DEN180044.pdf

[2] ACC/AHA/HRS, “2018 Guideline on Bradycardia and Cardiac Conduction Delay,” 2018. https://doi.org/10.1161/CIR.0000000000000628

[3] A. Amirshahi and M. Hashemi, “ECG Classification Algorithm Based on STDP and R-STDP Neural Networks for Real-Time Monitoring on Ultra Low-Power Personal Wearable Devices,” IEEE Transactions on Biomedical Circuits and Systems, vol. 13, no. 6, pp. 1483–1493, 2019. https://doi.org/10.1109/TBCAS.2019.2948920

[4] F. C. Bauer, D. R. Muir, and G. Indiveri, “Real-Time Ultra-Low Power ECG Anomaly Detection Using an Event-Driven Neuromorphic Processor,” IEEE Transactions on Biomedical Circuits and Systems, vol. 13, no. 6, pp. 1575–1582, 2019. https://doi.org/10.1109/TBCAS.2019.2953001

[5] J. Chen, F. Tian, J. Yang, and M. Sawan, “An Event-Driven Compressive Neuromorphic System for Cardiac Arrhythmia Detection,” 2022 IEEE International Symposium on Circuits and Systems (ISCAS), pp. 2690–2694, 2022. https://ieeexplore.ieee.org/document/9937756/

[6] D. Shanmugam, D. Blalock, and J. Guttag, “Multiple Instance Learning for ECG Risk Stratification,” Proceedings of the 4th Machine Learning for Healthcare Conference, PMLR, vol. 106, pp. 124–139, 2019. https://proceedings.mlr.press/v106/shanmugam19a.html

[7] M. Zihlmann, D. Perekrestenko, and M. Tschannen, “Convolutional Recurrent Neural Networks for Electrocardiogram Classification,” 2017 Computing in Cardiology (CinC), pp. 1–4, 2017. https://doi.org/10.22489/CinC.2017.070-060

[8] E. Zvuloni, R. Almog, M. Glikson, S. Brimer Biton, I. Green, I. Laufer, O. Amir, and J. A. Behar, “Modeling day-long ECG signals to predict heart failure risk with explainable AI,” npj Digital Medicine, vol. 9, article 486, 2026. https://doi.org/10.1038/s41746-026-02835-8

[9] PhysioNet, “MIT-BIH Normal Sinus Rhythm Database v1.0.0,” doi:10.13026/C2NK5R. https://physionet.org/content/nsrdb/1.0.0/

[10] PhysioNet, “BIDMC Congestive Heart Failure Database v1.0.0,” doi:10.13026/C29G60. https://physionet.org/content/chfdb/1.0.0/

[11] PhysioNet, “MIT-BIH Arrhythmia Database v1.0.0,” doi:10.13026/C2F305. https://physionet.org/content/mitdb/1.0.0/

[12] PhysioNet, “MIT-BIH Atrial Fibrillation Database v1.0.0,” doi:10.13026/C2MW2D. https://physionet.org/content/afdb/1.0.0/

[13] Goldberger AL et al., “PhysioBank, PhysioToolkit, and PhysioNet,” Circulation 101(23), 2000. https://doi.org/10.1161/01.CIR.101.23.e215

[14] Open Data Commons, “Attribution License v1.0.” https://opendatacommons.org/licenses/by/1-0/

# 부록 A. 핵심 수치

| 범주 | 수치 | Claim/scope |
|---|---|---|
| 입력 | signed 12-bit, 1 kSPS | CLM-002 |
| 시간축 | 60,000표본×30 | CLM-003 |
| Final chunk | 29/36=80.56%, F1 80.44% | CLM-004 |
| Record majority | 16/19=84.21%, F1 80.80% | CLM-005 |
| MATLAB | clipping 0%, min headroom 1.019633440086 V | CLM-015,024 |
| XMODEL | mean RMS 1.95 LSB, lag 0 | CLM-014 |
| Integration | SHA 36/36, gap=2 pred/mem 36/36 | CLM-012,013 |
| Pure RTL | 9719 LUT, 5038 FF, 0 BRAM, 0 DSP, WNS 8.184 ns | CLM-008,009 |
| MicroBlaze | 12494 LUT, 8494 reg, 16 BRAM, 3 DSP, WNS 0.097 ns | CLM-010 |
| Board | pred/mem 36/36; label 29/36 | CLM-011 |
| Streaming | 회피한 원시 입력 구간 2,700,000 bytes≈2.7 MB | CLM-023 |
| Benchmark | Exact C++ 1,777.699800 ms; RTL 54.012600 ms; 32.912687× estimate | CLM-018, CLM-043~CLM-047 |

# 부록 B. Claim/증거 mapping

| 본문 범주 | Claim | 핵심 증거 |
|---|---|---|
| Identity/interface/time hierarchy | CLM-001~003 | digital report, top RTL, 입력 contract |
| Evaluation/protocol | CLM-004~007,016~017 | lock/split/final metrics |
| Hardware/board | CLM-008~011 | Vivado and board artifacts |
| XMODEL/integration | CLM-012~014,025~027 | stress report and comparison CSV |
| MATLAB | CLM-015,024 | dynamic-range CSV/vector manifest |
| Benchmark/physical limits | CLM-018~022, CLM-043~047 | claim registry/benchmark import audit |
| Streaming memory | CLM-023 | direct RTL inventory |

전체 machine-readable 경로, 고정 commit, 담당자와 제한은 `reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv` 및 `source_of_truth/claim_registry.csv`를 따른다.

# 부록 C. 주요 artifact와 재현 절차

고정 component commit은 MATLAB `907f7e1...`, XMODEL `4756a508...`, digital `c6b80de...`다. PhysioNet raw source는 `tools/fetch_physionet_datasets.py`와 `tools/verify_physionet_datasets.py`로 저장소 밖에 복원한다. 통합 그림은 `tools/generate_integrated_figures.py`로 생성하며 보고서·저장소 checker를 연속 실행한다.

직접 architecture 증거:

- 사건 신호/QRS/RR: `components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v`, `qrs_lif_detector.v`, `pnn_rhythm_predictor.v`
- Rhythm: `rdm_variability_neuron.v`, `ectopic_pair_neuron.v`
- 파형 형태: `dscr_spike_counter.v`, `ram_peak_accumulator.v`, `qrs_maf_neuron.v`, `rbbb_qrs_delay_bank.v`
- Snapshot/final: `class_score_neurons.v`, `snn_ecg_30min_final_top.v`, `final_membrane_layer.v`
- 상태 inventory: `tables/streaming_state_inventory.csv`

```powershell
python tools/generate_integrated_figures.py
python tools/check_integrated_technical_report.py
python tools/check_integrated_repository.py
```

Application form의 page 제한, 소속·지도교수·서명 등 개인정보 입력은 이 public repository 밖의 private HWP 편집 단계에서 수행한다.

# 부록 D. Vivado FPGA 구현 근거

![그림 16. Post-route FPGA 구현과 hierarchy 배치](../figures/publication/FIG-P05_vivado_implementation/device_view_annotated_publication.svg)

*그림 16. 실제 Vivado Device View에 고정 routed checkpoint의 계층별 배치 셀 좌표를 정합한 post-route FPGA 구현 Figure. (a)는 SNN accelerator, MicroBlaze, local memory, 표본 공급기, AXI·UART·interrupt logic을 색으로 구분한 전체 system이며, (b)는 SNN accelerator에 속한 배치 셀만 분리 표시한다. (c)는 pure RTL과 MicroBlaze 통합 system의 자원·timing 범위를 구분한다. 색상은 실제 배치 좌표를 나타내지만 pblock 경계를 뜻하지 않으며, 본 그림은 ASIC layout이 아니다.*

![그림 17. MicroBlaze IP Integrator Block Design](../figures/publication/FIG-P05_vivado_implementation/microblaze_block_design.svg)

*그림 17. MicroBlaze, AXI interconnect, 표본 공급기, SNN accelerator, UART와 IRQ 연결. Vivado `write_bd_layout`의 native SVG를 raster 변환 없이 회전·여백만 정규화한 벡터다.*

![그림 18. Worst setup timing path](../figures/publication/FIG-P05_vivado_implementation/worst_setup_path.svg)

*그림 18. Vivado `write_schematic`으로 직접 export한 post-route 최악 setup path. data path delay 9.810 ns, requirement 10.000 ns, slack 0.097 ns이며 MicroBlaze 통합 system 범위다.*
