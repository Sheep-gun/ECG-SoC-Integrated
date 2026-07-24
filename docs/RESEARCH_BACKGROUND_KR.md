# 연구 배경

대표적인 ambulatory ECG 검사인 Holter는 24시간 이상 기록하여 짧은 측정에서 놓칠 수 있는 간헐적 이상을 찾는다. 웨어러블 장치에서 장시간 raw ECG 전체를 저장하고 전송하거나 대규모 dense model로 반복 분석하면 memory, computation과 communication 부담이 커질 수 있다.

본 연구는 ECG domain knowledge를 사건, 박동, 리듬과 파형 증거로 변환하고 이를 정수형 뉴런 상태에 누적하는 SNN 기반 streaming accelerator를 제안한다. 공개 데이터의 네 범주는 NSR, CHF, ARR, AF이며 임상 확정 진단이 아니라 source-database label을 뜻한다.
