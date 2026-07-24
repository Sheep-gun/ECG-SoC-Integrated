# 사전 feature 분석과 annotation 사용

## 목적

최종 feature를 임의로 정하지 않고 공개 ECG의 클래스별 차이를 사전에 분석해 하드웨어에서 추적 가능한 증거 후보를 선정했다. 원시 분석 자료와 그래프는 `analysis/feature_selection/`에 보존한다.

## 분석 절차

1. 원천 record와 공식 beat/rhythm annotation을 읽어 박동 위치와 구간 label을 정렬했다.
2. 한 record에서 파생한 구간이 다른 데이터 분할로 넘어가지 않도록 source-record ID를 유지했다.
3. RR 간격, pNN 계열 규칙성, 연속 RR 차이, early–late pair, ΔECG 방향 전환, R-peak 진폭, QRS 폭·복잡도와 말단 활동 후보를 계산했다.
4. boxplot, class summary와 간단한 분류 실험으로 클래스별 분포와 결측률을 확인했다.
5. 설명 가능성, 정수 연산 가능성, streaming state 크기와 분류 기여를 함께 고려해 최종 feature path를 정했다.

## 최종 RTL과의 대응

| 사전 분석 관점 | RTL 경로 | 최종 의미 |
|---|---|---|
| RR 규칙성 | PNN | 다음 RR이 예상 범위에 드는지 |
| 연속 RR 변화 크기 | RDM | 박동 간 리듬 변동 수준 |
| short–long pair | Ectopic Evidence | 조기·보상성 박동형 리듬 증거 |
| 기울기 방향 전환 | DSCR | 파형 굴곡·복잡도 |
| 예상 박동 부근 진폭 | RAM | QRS peak 크기 코드 |
| QRS 활동 폭·복잡도 | QRS MAF | 넓이·에너지·변화 구조 |
| QRS 후반 활동 | RBBB-like | 전도 지연성 파형 대리지표 |

최종 분류기는 annotation을 사용하지 않는다. annotation은 후보 탐색과 평가용이며, RTL 입력은 1 kSPS signed 12-bit ECG뿐이다.

## 해석 경계

이 feature들은 임상 진단 규칙을 그대로 구현한 것이 아니라 분류를 위한 공학적 대리지표다. 특히 RBBB-like는 우각차단 진단이 아니고, Ectopic Evidence도 특정 부정맥 확진이 아니다. feature 분석 결과만으로 임상적 인과나 일반화를 주장하지 않는다.
