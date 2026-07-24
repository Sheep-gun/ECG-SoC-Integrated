# Database–class confounding

NSR, CHF, ARR, AF는 각각 서로 다른 PhysioNet database에서 구성된다. 따라서 분류기가 질환 특징뿐 아니라 database별 측정환경, 전처리, 대상군 또는 장비 차이를 학습했을 가능성을 배제할 수 없다.

source-record-wise split은 동일 record에서 파생한 30분 chunk가 학습과 시험에 동시에 나타나는 leakage를 막지만 database–class confounding을 제거하지는 않는다. 현재 80.56%는 이 조건을 포함한 공개 데이터 기반 engineering result다.

후속 검증에는 동일 측정환경에서 네 범주를 수집한 장시간 cohort, 외부 database 평가와 clinical validation이 필요하다.
