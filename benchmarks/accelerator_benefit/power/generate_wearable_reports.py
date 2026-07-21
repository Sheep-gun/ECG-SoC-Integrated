#!/usr/bin/env python3
"""Generate bilingual wearable-power evidence reports and a comparison figure."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt


REPO = Path(__file__).resolve().parents[3]
BENCH = REPO / "benchmarks" / "accelerator_benefit"
POWER_RESULTS = BENCH / "power" / "results"
REPORTS = BENCH / "reports"
FIGURES = BENCH / "figures"


def f_w(value: float) -> str:
    return f"{value:.4f} W"


def f_mj(value: float) -> str:
    return f"{value:.4f} mJ"


def main() -> int:
    activity = json.loads((POWER_RESULTS / "activity_power_summary.json").read_text(encoding="utf-8"))
    ce = json.loads((POWER_RESULTS / "clock_enable_summary.json").read_text(encoding="utf-8"))
    budget = json.loads((POWER_RESULTS / "wearable_power_budget.json").read_text(encoding="utf-8"))
    groups = activity["groups"]
    burst = groups["baseline:burst_full_record"]
    stream = groups["baseline:streaming_1ksps_prefix"]
    opt_burst = groups["power_opt:burst_full_record"]
    opt_stream = groups["power_opt:streaming_1ksps_prefix"]

    b_total = burst["total_on_chip_power_w"]["median"]
    b_dyn = burst["dynamic_power_w"]["median"]
    b_ip_dyn = burst["accelerator_hierarchy_dynamic_power_w"]["median"]
    b_ip_total = burst["accelerator_plus_device_static_power_w"]["median"]
    b_energy = burst["accelerator_allocated_energy_per_decision_mj"]["median"]
    b_dyn_energy = burst["accelerator_dynamic_energy_per_decision_mj"]["median"]
    s_total = stream["total_on_chip_power_w"]["median"]
    s_dyn = stream["dynamic_power_w"]["median"]
    s_ip_dyn = stream["accelerator_hierarchy_dynamic_power_w"]["median"]
    s_ip_total = stream["accelerator_plus_device_static_power_w"]["median"]
    opt_b = opt_burst["total_on_chip_power_w"]["median"]
    opt_s = opt_stream["total_on_chip_power_w"]["median"]

    rows = budget["rows"]
    no_pg = next(float(row["power_w"]) for row in rows if row["scenario"] == "fpga_preloaded_burst_30min" and row["component"] == "Pure RTL FPGA without power gating")
    dyn_duty = next(float(row["power_w"]) for row in rows if row["scenario"] == "fpga_preloaded_burst_30min" and row["component"] == "Pure RTL dynamic subset")
    ideal_pg = next(float(row["power_w"]) for row in rows if row["scenario"] == "idealized_power_gated_ip")

    REPORTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    ko = f"""# 웨어러블 저전력 IP 근거 보강 결과

## 결론

현재 결과는 **100 MHz Artix-7에서 기능 정합된 ECG 가속기의 구현 후 저전력 가능성**을 뒷받침하지만, 목표 공정 ASIC의 post-layout 결과와 전체 wearable 부품 예산이 없으므로 “웨어러블용 저전력 반도체 IP”를 최종 입증한 단계는 아니다.

## 즉시 완료한 근거

| 항목 | 결과 | 분류 |
|---|---:|---|
| 실제 ECG burst top Total On-Chip Power 중앙값 | {f_w(b_total)} | ESTIMATED |
| 실제 ECG burst 가속기 hierarchy dynamic 중앙값 | {f_w(b_ip_dyn)} | ESTIMATED |
| 실제 ECG burst 가속기+FPGA static 할당 전력 | {f_w(b_ip_total)} | ESTIMATED |
| literal 100 MHz/1 kS/s top Total On-Chip Power 중앙값 | {f_w(s_total)} | ESTIMATED |
| literal 1 kS/s 가속기 hierarchy dynamic 중앙값 | {f_w(s_ip_dyn)} | ESTIMATED |
| literal 1 kS/s 가속기+FPGA static 할당 전력 | {f_w(s_ip_total)} | ESTIMATED |
| 36.0129 ms 기준 가속기 할당 energy/decision | {f_mj(b_energy)} | DERIVED |
| 36.0129 ms 기준 가속기 dynamic energy/decision | {f_mj(b_dyn_energy)} | DERIVED |
| 기존 CE + Vivado tool gating | {ce['slice_registers_percent_gated']:.3f}% ({ce['slice_registers_user_gated']} user + {ce['slice_registers_tool_gated']} tool / {ce['slice_registers_total']}) | ESTIMATED |
| power_opt burst top | {f_w(opt_b)} | ESTIMATED |
| power_opt 1 kS/s top | {f_w(opt_s)} | ESTIMATED |
| FPGA rail idle/active 차동 | 미측정 | NOT MEASURED |
| 55/65/28 nm ASIC post-layout | PDK/tool 부재 | NOT AVAILABLE |

네 클래스에서 각각 실제 1,800,000샘플 burst SAIF와 실제 100샘플 literal 1 kS/s SAIF를 생성했다. 모든 burst 캡처는 잠긴 final prediction과 네 membrane 값을 통과했다. RTL SAIF의 routed-net 매칭률은 약 12%이며 나머지는 Vivado vectorless propagation이므로 confidence는 Medium이다. 따라서 이 결과는 기존 완전 vectorless 값보다 workload 관련성이 높지만 sign-off activity power는 아니다.

## Streaming과 preloaded burst 해석

- streaming은 100 MHz global clock가 계속 동작한다. 따라서 1 kS/s로 입력 활동이 낮아져도 FPGA static과 clock power가 남는다.
- 30분 레코드를 36.0129 ms에 burst 처리하고 나머지 시간을 clock-gate한다고 가정하면, power-gating이 없는 평균은 약 {no_pg * 1000:.3f} mW이며 대부분 FPGA static이다.
- accelerator dynamic만 duty-cycle한 항은 약 {dyn_duty * 1e6:.3f} uW이다.
- static까지 완전히 제거하는 이상적 power-gating 상한은 약 {ideal_pg * 1e6:.3f} uW지만 retention, isolation, wake energy, switch leakage가 모두 빠져 있어 제품 수치로 사용할 수 없다.

## Wearable 전체 예산

MAX30001의 85 uW ECG AFE는 외부 datasheet reference로만 포함했다. 실제 sample memory, MCU, BLE와 PMIC는 부품·전압·duty cycle이 정해지지 않아 빈 stage gate로 남겼다. 따라서 현재 전체 wearable subtotal이나 배터리 수명은 제시하지 않는다.

## 남은 필수 근거

1. 목표 55/65/28 nm PDK/Liberty/LEF와 extracted parasitic을 사용한 post-layout leakage/dynamic power
2. UPF/CPF 기반 retention·isolation·power-switch 및 wake overhead
3. 실제 선정 MCU/BLE/memory/PMIC workload와 전체 전력 예산
4. 외부 계측기로 동일 BIT/ELF의 idle/stream/burst rail 차동 실측

물리 보드 전력은 측정하지 않았으며, 모든 Vivado 값은 **ESTIMATED**, 전력과 latency의 곱은 **DERIVED**이다.
"""
    en = f"""# Wearable Low-Power IP Evidence Extension

## Conclusion

The evidence now supports a functionally matched ECG accelerator's low-power potential on a 100 MHz Artix-7 implementation. It does not yet prove a wearable low-power semiconductor IP claim because target-node ASIC post-layout power and a complete wearable component budget are unavailable.

## Evidence completed now

| Item | Result | Class |
|---|---:|---|
| Real-ECG burst top Total On-Chip Power median | {f_w(b_total)} | ESTIMATED |
| Real-ECG burst accelerator-hierarchy dynamic median | {f_w(b_ip_dyn)} | ESTIMATED |
| Real-ECG burst accelerator plus allocated FPGA static | {f_w(b_ip_total)} | ESTIMATED |
| Literal 100 MHz/1 kS/s top Total On-Chip Power median | {f_w(s_total)} | ESTIMATED |
| Literal 1 kS/s accelerator-hierarchy dynamic median | {f_w(s_ip_dyn)} | ESTIMATED |
| Literal 1 kS/s accelerator plus allocated FPGA static | {f_w(s_ip_total)} | ESTIMATED |
| Accelerator allocated energy at 36.0129 ms | {f_mj(b_energy)} | DERIVED |
| Accelerator dynamic energy at 36.0129 ms | {f_mj(b_dyn_energy)} | DERIVED |
| Existing CE plus Vivado tool gating | {ce['slice_registers_percent_gated']:.3f}% ({ce['slice_registers_user_gated']} user + {ce['slice_registers_tool_gated']} tool / {ce['slice_registers_total']}) | ESTIMATED |
| Power-optimized burst top | {f_w(opt_b)} | ESTIMATED |
| Power-optimized 1 kS/s top | {f_w(opt_s)} | ESTIMATED |
| FPGA idle/active rail delta | not measured | NOT MEASURED |
| 55/65/28 nm ASIC post-layout | blocked by missing PDK/tools | NOT AVAILABLE |

Four class-representative full 1,800,000-sample burst SAIF traces and four literal 1 kS/s, 100-sample traces use real ECG data. Every burst capture passed locked final-prediction and four-membrane checks. RTL-to-routed SAIF coverage is approximately 12%; Vivado uses vectorless propagation for the remaining nets, so confidence remains Medium. This is workload-relevant estimation, not sign-off activity power.

## Streaming versus preloaded burst

- Streaming leaves the 100 MHz global clock active, so FPGA static and clock power dominate even at 1 kS/s.
- If a 30-minute record is burst-processed in 36.0129 ms and only the clock is gated afterward, average power is approximately {no_pg * 1000:.3f} mW because FPGA static remains.
- The duty-cycled accelerator dynamic term alone is approximately {dyn_duty * 1e6:.3f} uW.
- An idealized full-power-gating upper bound is approximately {ideal_pg * 1e6:.3f} uW, but excludes retention, isolation, wake energy, switch leakage and off-state leakage, so it is not a product number.

The 85 uW MAX30001 ECG AFE is included only as an external datasheet reference. Sample memory, MCU, BLE and PMIC remain explicit stage gates until the parts and workloads are selected. Physical board power was not measured. Vivado values are **ESTIMATED** and power-times-latency values are **DERIVED**.
"""
    (REPORTS / "WEARABLE_LOW_POWER_EVIDENCE_KO.md").write_text(ko, encoding="utf-8")
    (REPORTS / "WEARABLE_LOW_POWER_EVIDENCE_EN.md").write_text(en, encoding="utf-8")

    labels = ["Burst\nbaseline", "1 kS/s\nbaseline", "Burst\npower_opt", "1 kS/s\npower_opt"]
    total_values = [b_total * 1000, s_total * 1000, opt_b * 1000, opt_s * 1000]
    ip_dynamic_values = [
        b_ip_dyn * 1000,
        s_ip_dyn * 1000,
        opt_burst["accelerator_hierarchy_dynamic_power_w"]["median"] * 1000,
        opt_stream["accelerator_hierarchy_dynamic_power_w"]["median"] * 1000,
    ]
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=180)
    x = range(len(labels))
    ax.bar([i - 0.18 for i in x], total_values, width=0.36, label="Top total on-chip", color="#4472C4")
    ax.bar([i + 0.18 for i in x], ip_dynamic_values, width=0.36, label="Accelerator hierarchy dynamic", color="#70AD47")
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("Vivado estimated power (mW)")
    ax.set_title("Real-ECG SAIF Power: Burst vs 1 kS/s")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    ax.text(0.01, -0.18, "Post-route, 100 MHz, Medium confidence, ~12% routed-net SAIF match; not physical board power.", transform=ax.transAxes, fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES / "wearable_power_modes.png", bbox_inches="tight")
    plt.close(fig)
    print(REPORTS / "WEARABLE_LOW_POWER_EVIDENCE_KO.md")
    print(REPORTS / "WEARABLE_LOW_POWER_EVIDENCE_EN.md")
    print(FIGURES / "wearable_power_modes.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
