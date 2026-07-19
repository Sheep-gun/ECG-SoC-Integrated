# 통합 검증

## 검증 사슬

| Boundary | Input evidence | Output evidence | Acceptance |
|---|---|---|---|
| MATLAB nominal | class별 input/reference package | frequency/headroom/coding CSV | nominal intent와 signed vector가 manifest로 고정 |
| MATLAB/LTspice | nominal parameter와 vector | `.asc`/`.net`, AC/transient/S&H/ADC/stress 결과 | 목표 응답과 실제 schematic의 정합 |
| LTspice/XMODEL | 동일 10초 ECG와 ADC contract | 10,000-code error/coverage table | MAE 0.6445 LSB, corr. 0.999518, ±5 LSB 98.74%, ±10 LSB 99.89% |
| XMODEL 장시간 | fixed 회로 계약과 public ECG | 36×60초 waveform/stress reports | 평균 RMS 1.95 LSB, lag 0; 10초 LTspice 비교와 별도 범위 |
| XMODEL/digital | full-record AFE stream | 30분 chunk와 SHA256 CSV | board-replay input과 36/36 byte identity |
| AFE/locked RTL | same 36 chunks | final_pred/final_mem compare CSV | gap=2에서 36/36 bit-exact |
| Python/RTL | locked model and parameters | XSim final outputs | final-test mismatch 0/36 |
| RTL/IP/Vivado | synthesizable sources | utilization/timing/package metadata | positive timing closure와 IP-XACT package |
| XSim/FPGA | same replay inputs and expected outputs | UART/parsed/batch artifacts | board pred/mem 36/36 equivalence |

## Canonical AFE-to-digital result

`components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv`의 36개 모든 row는 다음 조건을 만족한다.

- `input_sha256_match=true`
- `sample_gap_cycles=2`
- `samples_driven=accepted_samples=1800000`
- `windows=30`, `decisions=1`
- `pred_match=true`, `mem_match=true`

따라서 AFE-generated chunk와 digital board input이 같은 bytes이고, canonical cadence에서 locked RTL이 같은 final state를 재현했음을 말할 수 있다.

## 서로 다른 36/36의 구분

1. Input SHA256 36/36: 두 input artifact의 byte identity
2. AFE-to-RTL 36/36: canonical XSim에서 digital golden reproduction
3. Board 36/36: FPGA output과 full-top XSim expected output의 functional equivalence
4. Label accuracy 29/36: output class와 ground-truth public-dataset label의 일치

앞의 세 결과를 더해 classification accuracy 100%라고 표현하지 않는다.

## Reproducibility evidence

Imported component bytes는 `artifact_manifest.csv`의 SHA256으로 검증한다. Upstream origin, active HEAD와 fixed imported commit은 `upstream_commits.yaml` 및 전후 status JSON에 기록한다. Import tool은 Git object archive를 사용하므로 concurrent benchmark worktree bytes를 읽지 않는다.

## Remaining gaps

- LTspice schematic은 검증했으나 physical AFE/ADC와 silicon validation 없음
- same-acquisition multi-class clinical cohort 없음
- database-class confounding 미해소
- digital `main` commit `09e4d840...`의 independent NO_BOARD accelerator-benefit benchmark 반입 완료; physical board timing·power는 대기
- external report HWP 작성은 private downstream task
