# 장시간 ECG 관련 연구 검증 기록

## 검증 원칙

통합 보고서 제2.1절에 사용하는 관련 연구는 원 논문, 공식 출판 페이지 또는 저자 원고에서 방법과 최종 판정 단위를 직접 확인하였다. 서로 다른 과업의 정확도를 순위처럼 비교하지 않는다. 아래의 `확인 범위`는 본 프로젝트와 비교할 수 있는 입력 단위, 장시간 집계와 구현 형태만 기록한다.

## RW-001 Amirshahi–Hashemi STDP/R-STDP

- 정식 제목: *ECG Classification Algorithm Based on STDP and R-STDP Neural Networks for Real-Time Monitoring on Ultra Low-Power Personal Wearable Devices*
- 저자/연도: Alireza Amirshahi, Matin Hashemi, 2019
- 출판: IEEE Transactions on Biomedical Circuits and Systems, 13(6), 1483–1493
- DOI: https://doi.org/10.1109/TBCAS.2019.2948920
- 저자 원고: https://arxiv.org/abs/1905.02954
- 확인 범위: R-peak 전 0.25초와 후 0.45초의 개별 심박을 입력으로 사용한다. 심박을 겹치는 구간으로 나누고 진폭에 비례하는 Poisson spike train으로 변환한다. STDP 계층은 spike timing 특징을 학습하고 R-STDP 출력 계층은 reward/punishment로 개별 심박 클래스를 학습한다.
- 경계: 장시간 기록의 여러 Snapshot을 기록 단위 질환 클래스로 집계하지 않는다.
- 거시적 비교: 이 연구는 “한 심박이 어떤 종류인가”를 묻고, 본 연구는 “여러 구간을 포함한 기록 전체가 NSR·CHF·ARR·AFF 중 무엇인가”를 묻는다.

## RW-002 Bauer–Muir–Indiveri event-driven anomaly detector

- 정식 제목: *Real-Time Ultra-Low Power ECG Anomaly Detection Using an Event-Driven Neuromorphic Processor*
- 저자/연도: Felix Christian Bauer, Dylan Richard Muir, Giacomo Indiveri, 2019
- 출판: IEEE Transactions on Biomedical Circuits and Systems, 13(6), 1575–1582
- DOI: https://doi.org/10.1109/TBCAS.2019.2953001
- PubMed: https://pubmed.ncbi.nlm.nih.gov/31715572/
- 확인 범위: 연속 다채널 ECG를 asynchronous binary event로 변환하고 recurrent SNN reservoir와 event-driven linear readout으로 처리한다. 병리별 readout firing activity를 저역통과한 뒤 문턱 초과 여부로 binary anomaly trigger를 만든다. DYNAP chip에서 검증하였다.
- 경계: 연속 감시와 시간 필터링은 수행하지만, 다중 질환의 Snapshot 증거를 기록 단위 클래스 상태로 누적하지 않는다.
- 거시적 비교: 이 연구는 “지금 병리 패턴이 나타났는가”를 이진 신호로 알리고, 본 연구는 발견한 여러 질환 구간을 모아 기록 전체의 네 클래스를 정한다.

## RW-003 Chen et al. LC-ADC+SCNN

- 정식 제목: *An Event-Driven Compressive Neuromorphic System for Cardiac Arrhythmia Detection*
- 저자/연도: Jinbo Chen, Fengshi Tian, Jie Yang, Mohamad Sawan, 2022
- 출판: 2022 IEEE International Symposium on Circuits and Systems, 2690–2694
- 공식 출판 경로: https://ieeexplore.ieee.org/document/9937756/
- 저자 원고: https://arxiv.org/abs/2205.13292
- 확인 범위: level-crossing ADC는 ECG가 양자화 level을 넘을 때 방향 spike를 만들고, SCNN은 spike를 직접 받아 convolution/fully-connected 계층과 출력 spike counter로 분류한다. 논문의 MIT-BIH 평가는 선택한 개별 beat를 N·SVEB·VEB·F로 분류한다.
- 경계: sensing–processing 공동설계와 입력 압축이 중심이며, 장시간 record-level 집계는 없다. 논문 결과는 simulation 기반이다.
- 거시적 비교: 사건 기반 입력이라는 공통점은 있지만 최종 출력은 개별 심박 클래스이며, 본 연구처럼 장시간 기록 전체의 클래스를 판정하지 않는다.

## RW-004 Shanmugam et al. multiple instance learning

- 정식 제목: *Multiple Instance Learning for ECG Risk Stratification*
- 저자/연도: Divya Shanmugam, Davis Blalock, John Guttag, 2019
- 출판: Proceedings of the 4th Machine Learning for Healthcare Conference, PMLR 106, 124–139
- 공식 출판 경로: https://proceedings.mlr.press/v106/shanmugam19a.html
- 확인 범위: 약 48시간 ECG에서 R-peak 주위 1초 심박을 정렬하고 연속 심박 묶음을 instance로 만든다. instance별 확률 중 높은 20%를 평균해 patient-level cardiovascular-death risk score를 만든다. 대부분의 심박이 정상처럼 보여도 일부 병리적 beat sequence의 비율이 위험을 나타낼 수 있다는 collective assumption을 사용한다.
- 경계: 본 연구와 국소 위험 instance 집계 개념은 유사하지만, 출력은 이진 예후 위험도이고 software MIL이다.
- 거시적 비교: 대부분 정상인 긴 기록에서 일부 중요한 구간을 찾는 방향은 매우 유사하다. 다만 이 연구는 미래 심혈관 사망 위험을, 본 연구는 현재 ECG 기록의 네 클래스를 출력한다.

## RW-005 Zihlmann et al. variable-length four-class ECG

- 정식 제목: *Convolutional Recurrent Neural Networks for Electrocardiogram Classification*
- 저자/연도: Martin Zihlmann, Dmytro Perekrestenko, Michael Tschannen, 2017
- 출판: 2017 Computing in Cardiology, 1–4
- DOI: https://doi.org/10.22489/CinC.2017.070-060
- 저자 원고: https://www.mins.ee.ethz.ch/pubs/files/cinc2017.pdf
- 확인 범위: 9–61초 가변 길이 단일유도 ECG에서 CNN이 특징을 추출하고, 시간 평균 또는 3-layer bidirectional LSTM이 기록 전체 특징을 통합한다. 출력은 normal rhythm, AF rhythm, other rhythm, noisy recording의 네 클래스다.
- 경계: 기록 단위 4-class 구조는 이미 존재한다. 본 연구와 클래스 정의, 길이, 내부 상태의 설명 가능성, RTL/IP 구현이 다르다.
- 거시적 비교: 이 연구는 짧은 기록 자체를 네 리듬 범주로 분류하며, 수시간 기록에서 드물게 나타나는 구간을 찾아 장시간 판정으로 연결하는 문제는 중심이 아니다.

## RW-006 DeepHHF

- 정식 제목: *Modeling day-long ECG signals to predict heart failure risk with explainable AI*
- 저자/연도: Eran Zvuloni, Ronit Almog, Michael Glikson, Shany Brimer Biton, Ilan Green, Izhar Laufer, Offer Amir, Joachim A. Behar, 2026
- 출판: npj Digital Medicine, volume 9, article 486
- DOI: https://doi.org/10.1038/s41746-026-02835-8
- 출판 상태: 2026년 5월 24일 accepted된 정식 journal article. 이전 arXiv 원고만을 근거로 사용하지 않는다.
- 확인 범위: 24시간 단일유도 Holter에서 30초 window encoder를 먼저 학습하고, frozen encoder가 만든 시간 순서 특징을 Transformer sequential head로 통합해 전체 Holter의 5년 HF 위험 score를 출력한다. 논문 방법에서는 24시간당 720개 window sequence를 사용한다.
- 경계: 실제 24시간 window-to-record 통합의 검증 가능한 사례지만, binary prognosis software model이며 NSR·CHF·ARR·AFF RTL classifier가 아니다.
- 거시적 비교: 장시간 ECG를 짧은 구간으로 나누고 다시 하나의 결과로 합치는 흐름은 검토한 연구 중 본 연구와 가장 유사하다. DeepHHF는 향후 5년 심부전 위험을 예측하고, 본 연구는 현재 기록이 NSR·CHF·ARR·AFF 가운데 어느 클래스인지 판정한다. DeepHHF는 24시간 입력을 사용했지만 본 연구의 현재 검증 범위는 30분이다.

## 통합 비교 경계

검토한 대표 선행연구는 개별 심박 SNN, 연속 ECG anomaly trigger, event-driven input compression, patient-level MIL, 가변 길이 CNN/LSTM, 24시간 Transformer 통합을 각각 보여준다. 이 검토 범위에서는 다음 요소를 한 시스템에 함께 적용한 사례를 확인하지 못했다.

- NSR·CHF·ARR·AFF 기록 단위 분류
- Snapshot별 리듬·파형 형태·질환 증거의 명시적 고정 폭 상태화
- 간헐적 강한 Snapshot의 출현 빈도·반복성과 장시간 일관성 누적
- RTL/IP/FPGA 구현
- MATLAB–XMODEL–signed stream–RTL 추적성

이는 세계 최초 또는 문헌 전체에 동일 연구가 없다는 주장이 아니다. 현재 실제 검증 입력은 30분이며 24시간 정확도·처리시간·전력은 미검증이다.
