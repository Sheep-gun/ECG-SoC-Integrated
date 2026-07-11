# Database–class confounding

## 공개해야 하는 사실

1. NSR, CHF, ARR, AFF는 각각 nsrdb, chfdb, mitdb, afdb라는 서로 다른 공개 source database에서 왔다.
2. Strict source-record-wise split은 동일한 physical source record가 train, validation, final-test partition을 넘나드는 것을 방지한다.
3. 이 분리는 direct record leakage를 방지하지만 database-to-class confounding을 제거하지 않는다.
4. Database별 acquisition condition, amplitude scale, noise, preprocessing, lead configuration, sampling과 record distribution 차이가 classification에 기여했을 수 있다.
5. Database name, record ID, filename, path, partition과 split metadata는 classifier input feature로 사용하지 않았다.
6. 모든 class를 공통 1 kSPS signed 12-bit stream convention으로 변환했지만 이 변환이 database-domain 차이를 제거했다고 증명하지는 않는다.
7. 보고 accuracy는 현재 public-dataset composition 아래의 engineering result이다.
8. 이 결과는 clinical disease generalization의 증거로 해석할 수 없다.
9. 더 강한 검증에는 동일 acquisition environment의 multi-class cohort 또는 명시적인 cross-database/domain-generalization protocol이 필요하다.

## Leakage와 confounding의 차이

Record leakage는 같은 source record의 일부가 학습과 시험 양쪽에 들어가 sample similarity가 직접 공유되는 문제다. Source-record-wise split은 이를 구조적으로 막는다. Database-class confounding은 class label이 database identity와 결합되어, model이 의도한 physiology뿐 아니라 acquisition/domain 특성을 사용할 가능성이다. 서로 다른 문제이므로 record leakage를 막았다는 사실만으로 confounding이 해결됐다고 말할 수 없다.

## 공통 stream convention의 의미

Resampling, AFE/ADC-compatible processing과 signed 12-bit coding은 interface와 hardware verification condition을 통일한다. 이는 각 class에 같은 digital contract를 적용했다는 뜻이다. 그러나 원 waveform의 lead, subject population, noise와 recording equipment 차이가 모두 사라졌음을 뜻하지 않는다.

## 영향을 받는 claim

이 한계는 80.56%/84.21% classification result의 generalization 해석과 네 class physiology claim의 강도에 영향을 준다. 따라서 현 결과를 임상 cohort에 바로 일반화하거나 CHF 진단 능력으로 표현하지 않는다.

반면 이 한계가 다음 engineering evidence를 무효화하지는 않는다.

즉 same-acquisition cohort가 아직 없다는 사실은 generalization의 한계이며, 이미 같은 입력으로 검증한 RTL correctness의 한계와 동일하지 않다.

- RTL이 locked integer reference를 구현했는지 여부
- same-input final_pred/final_mem bit-exact equivalence
- AXI/IP-XACT packaging
- FPGA full-record replay
- streaming Snapshot/Final Membrane architecture
- Vivado resource와 timing-closure evidence

## 향후 검증

우선순위는 동일 acquisition/lead 조건에서 네 label을 포함하는 cohort, class와 DB를 분리할 수 있는 cross-database split, database-prediction diagnostic, 그리고 train/validation만 사용한 trivial-statistics baseline이다. 기존 locked final-test를 재튜닝에 사용해서는 안 된다.
