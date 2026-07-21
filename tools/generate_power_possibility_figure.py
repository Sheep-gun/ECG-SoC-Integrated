#!/usr/bin/env python3
"""Generate the report-facing FPGA power and ideal power-gating figure."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[1]
ACTIVITY = ROOT / "benchmarks" / "accelerator_benefit" / "power" / "results" / "activity_power_summary.json"
BUDGET = ROOT / "benchmarks" / "accelerator_benefit" / "power" / "results" / "wearable_power_budget.csv"
OUTPUT_PNG = ROOT / "figures" / "final" / "FIG-12b_power_energy.png"


def configure_font() -> None:
    for candidate in [Path("C:/Windows/Fonts/malgun.ttf"), Path("C:/Windows/Fonts/NanumGothic.ttf")]:
        if candidate.is_file():
            font_manager.fontManager.addfont(str(candidate))
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(candidate)).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


def load_values() -> dict[str, float]:
    activity = json.loads(ACTIVITY.read_text(encoding="utf-8-sig"))
    burst = activity["groups"]["baseline:burst_full_record"]
    streaming = activity["groups"]["baseline:streaming_1ksps_prefix"]
    with BUDGET.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ideal = next(row for row in rows if row["scenario"] == "idealized_power_gated_ip" and row["component"] == "Pure RTL FPGA-equivalent IP")
    return {
        "static_mw": burst["device_static_power_w"]["median"] * 1000,
        "burst_dynamic_mw": burst["accelerator_hierarchy_dynamic_power_w"]["median"] * 1000,
        "burst_total_mw": burst["accelerator_plus_device_static_power_w"]["median"] * 1000,
        "stream_dynamic_mw": streaming["accelerator_hierarchy_dynamic_power_w"]["median"] * 1000,
        "stream_total_mw": streaming["accelerator_plus_device_static_power_w"]["median"] * 1000,
        "active_latency_ms": 36.0129,
        "energy_mj": 5.38392855,
        "ideal_uw": float(ideal["power_w"]) * 1_000_000,
    }


def main() -> int:
    configure_font()
    v = load_values()
    fig = plt.figure(figsize=(13.2, 7.1), facecolor="white")
    grid = fig.add_gridspec(1, 2, width_ratios=[1.08, 1.0], left=0.075, right=0.97, top=0.82, bottom=0.19, wspace=0.28)

    ax = fig.add_subplot(grid[0, 0])
    labels = ["실시간 1 kS/s\n100-sample trace", "Burst 활성 구간\n30분 입력 처리"]
    dynamic = [v["stream_dynamic_mw"], v["burst_dynamic_mw"]]
    static = [v["static_mw"], v["static_mw"]]
    totals = [v["stream_total_mw"], v["burst_total_mw"]]
    x = [0, 1]
    ax.bar(x, static, width=0.58, color="#9aa8ba", label="FPGA device static")
    ax.bar(x, dynamic, width=0.58, bottom=static, color="#2f73bf", label="가속기 hierarchy dynamic")
    for xpos, total, dyn in zip(x, totals, dynamic):
        ax.text(xpos, total + 4.0, f"{total:.1f} mW", ha="center", va="bottom", fontsize=14, fontweight="bold", color="#18324f")
        ax.text(xpos, v["static_mw"] / 2, f"정적 {v['static_mw']:.0f}", ha="center", va="center", fontsize=11, color="white", fontweight="bold")
        ax.text(xpos, v["static_mw"] + dyn / 2, f"동적 {dyn:.1f}", ha="center", va="center", fontsize=11, color="white", fontweight="bold")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 170)
    ax.set_ylabel("Vivado 추정전력 (mW)", fontsize=12)
    ax.set_title("(a) 현재 FPGA 구현의 동작 전력", fontsize=15, fontweight="bold", pad=16)
    ax.grid(axis="y", alpha=0.22)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper left", frameon=False, fontsize=10)

    ax2 = fig.add_subplot(grid[0, 1])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis("off")
    ax2.set_title("(b) 완전 power-gating 적용 가능성", fontsize=15, fontweight="bold", pad=16)

    box_style = dict(boxstyle="round,pad=0.65", linewidth=1.8)
    ax2.text(0.5, 0.78, f"활성 구간\n{v['burst_total_mw']:.1f} mW × {v['active_latency_ms']:.4f} ms", ha="center", va="center", fontsize=14, bbox={**box_style, "facecolor": "#e8f1fb", "edgecolor": "#2f73bf"})
    ax2.annotate("", xy=(0.5, 0.61), xytext=(0.5, 0.69), arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#334155"))
    ax2.text(0.5, 0.54, f"30분 ECG 1회 판정\n활성 에너지 {v['energy_mj']:.3f} mJ", ha="center", va="center", fontsize=14, bbox={**box_style, "facecolor": "#eef7ee", "edgecolor": "#4e9a51"})
    ax2.annotate("÷ 1,800 s", xy=(0.5, 0.34), xytext=(0.5, 0.44), ha="center", va="center", fontsize=12, arrowprops=dict(arrowstyle="-|>", lw=1.8, color="#334155"))
    ax2.text(0.5, 0.23, f"이상적 연산 코어 평균\n{v['ideal_uw']:.2f} µW", ha="center", va="center", fontsize=18, fontweight="bold", bbox={**box_style, "facecolor": "#fff2df", "edgecolor": "#e58a1f"})
    ax2.text(0.5, 0.06, "현재 FPGA 전력이 아닌 완전 power-gating 파생값", ha="center", va="center", fontsize=11, color="#a33a2b", fontweight="bold")

    fig.suptitle("실제 ECG 기반 FPGA 전력과 저전력 ASIC 구현 가능성", fontsize=23, fontweight="bold", color="#142b47", y=0.94)
    fig.text(0.075, 0.105, "근거: 100 MHz real-ECG SAIF Vivado post-route estimate · routed-net match 약 12% · confidence Medium", fontsize=10.5, color="#465569")
    fig.text(0.075, 0.062, "2.99 µW 제외 항목: 입력 메모리, retention, isolation, power switch, wake energy, off-state leakage, AFE·ADC·MCU·BLE·PMIC", fontsize=10.5, color="#465569")

    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PNG, dpi=180, facecolor="white")
    plt.close(fig)
    print(f"wrote {OUTPUT_PNG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
