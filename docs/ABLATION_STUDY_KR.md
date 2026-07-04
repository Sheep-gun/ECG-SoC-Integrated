# Ablation Study

## 1. 왜 ablation이 필요한가

이 프로젝트는 단일 threshold classifier가 아니라, 60초 Snapshot Readout과 30분 Final Membrane Readout이 결합된 구조이다. 따라서 어떤 구조가 실제 성능에 기여하는지 분리해서 보여줘야 한다.

## 2. 실행한 ablation

실행:

```powershell
python tools\run_ablation_suite.py
```

결과:

- `reports/award_readiness/ablation_summary.md`
- `reports/award_readiness/ablation_summary.csv`
- `reports/award_readiness/figures/ablation_accuracy_bar.png`

## 3. 결과 요약

| experiment | status | correct | accuracy | 의미 |
|---|---|---:|---:|---|
| full_model | Measured | 125/136 | 91.91% | train/val/test 전체 fixed Python golden |
| arr_focus_no_margin | Measured | 124/136 | 91.18% | 마지막 AFF->ARR margin evidence 제거 |
| base_final | Measured | 120/136 | 88.24% | ARR-focus post rule 제거 |
| snapshot_majority | Measured | 103/136 | 75.74% | 30개 snapshot majority만 사용 |
| snapshot_mem_sum | Measured | 101/136 | 74.26% | snapshot membrane sum만 사용 |
| feature_sum_zeroed | Limited | 84/136 | 61.76% | final-layer evidence sum만 zero |

이 결과는 final membrane accumulation과 evidence current가 snapshot-only 구조보다 유의미하게 기여한다는 engineering evidence이다.

## 4. 제한

`feature_sum_zeroed`는 final-layer evidence rule에 들어가는 누적 feature sum을 zero로 만든 제한적 ablation이다. snapshot RTL 내부 feature extractor를 제거한 RTL 합성 ablation이 아니다.

아직 수행하지 않은 항목:

- raw/AFE-off full-record end-to-end accuracy
- HPF/notch/LPF-off `.mem` 재생성 후 accuracy
- feature module별 RTL 제거 및 synthesis/resource ablation

이 항목들은 `reports/award_readiness/ablation_summary.csv`에서 TODO로 남겼다.
