# 디지털 등가 모델

`digital_equivalence/`에는 RTL과 같은 정수 연산을 수행하는 독립 기준 모델과 비교 결과를 둔다.

| 하위 경로 | 내용 |
|---|---|
| `digital_equivalence/tools/` | Python 기준 모델, 36-case 등가성 검사와 benchmark |
| `digital_equivalence/exact_cpp/` | Exact C++ 모델, 내부 상태 및 trace 비교 |
| `digital_equivalence/reference/` | 잠금 기준값과 parameter |
| `digital_equivalence/results/` | 재현된 비교 결과 |
| `digital_equivalence/reports/` | 방법과 수치 해석 범위 |
