# Performance Baseline

## 1. 목적

accuracy만으로는 accelerator IP의 설득력이 부족하다. 본 문서는 CPU/Python final-readout baseline, RTL cycle count, Vivado resource/timing/power estimate를 한곳에 묶어 정리한다.

## 2. 실행 결과

```powershell
python tools\benchmark_cpu_vs_rtl.py --repeats 3
python tools\collect_vivado_metrics.py
```

결과:

- `reports/award_readiness/cpu_vs_rtl_summary.md`
- `reports/award_readiness/cpu_baseline_latency.csv`
- `reports/award_readiness/vivado_metrics.md`
- `reports/award_readiness/vivado_metrics.json`

## 3. CPU/Python baseline

현재 Python timing은 raw ECG sample을 모두 처리하는 CPU baseline이 아니라, 기존 XSim/Python flow가 만든 **precomputed chunk feature/final-readout inference**를 측정한다. 따라서 raw-sample CPU classifier보다 훨씬 빠르게 보일 수 있고, 이를 end-to-end CPU speedup으로 말하면 안 된다.

보고 가능한 표현:

> Python final-readout baseline은 precomputed chunk feature를 입력으로 하는 local script latency이다. RTL throughput은 profile counter와 Vivado timing에서 derived estimate로 계산했다.

## 4. RTL cycle/resource evidence

| 항목 | 값 |
|---|---:|
| accepted samples / 30min chunk | 1,800,000 |
| total cycles / chunk | 1,800,480 |
| cycles/sample total | 1.000267 |
| AXI OOC WNS @10ns | 0.081 ns |
| locked pure RTL LUT/FF/BRAM/DSP | 9719 / 5038 / 0 / 0 |
| Vivado estimated total power | 0.099 W |

Vivado power는 post-implementation estimate이며 실제 보드 전류 측정값이 아니다.

## 5. 금지 표현

- CPU보다 몇 배 빠르다고 단정하지 않는다. 현재 CPU baseline은 end-to-end raw sample baseline이 아니다.
- energy/sample을 실측값처럼 말하지 않는다.
- MicroBlaze smoke system resource를 accelerator core resource처럼 비교하지 않는다.
