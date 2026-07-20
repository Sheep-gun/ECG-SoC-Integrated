#!/usr/bin/env python3
"""Generate Section 4 digital/integration figures and concise result tables."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "figures" / "final"
TABLES = ROOT / "tables"
VALIDATION = ROOT / "validation" / "digital_section4"


def esc(value: object) -> str:
    return html.escape(str(value))


def text(x: float, y: float, value: object, size: int = 18, weight: int = 400,
         anchor: str = "start", color: str = "#182230") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
        'font-family="Arial, Noto Sans KR, Malgun Gothic, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{esc(value)}</text>'
    )


def canvas(width: int, height: int, title: str, description: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(description)}">',
        f'<title>{esc(title)}</title>',
        f'<desc>{esc(description)}</desc>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        text(width / 2, 48, title, 28, 700, "middle"),
    ]


def box(lines: list[str], x: float, y: float, w: float, h: float, title: str,
        body: list[str], fill: str, stroke: str) -> None:
    lines.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )
    lines.append(text(x + w / 2, y + 34, title, 19, 700, "middle"))
    for i, item in enumerate(body):
        lines.append(text(x + w / 2, y + 68 + i * 27, item, 16, 500, "middle", "#344054"))


def arrow(lines: list[str], x1: float, y1: float, x2: float, y2: float) -> None:
    lines.append(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        'stroke="#475467" stroke-width="2.5" marker-end="url(#arrow)"/>'
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def bool_true(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def binary_wave(lines: list[str], trace: dict, signal_names: list[tuple[str, str]],
                x: float, y: float, w: float, h: float) -> None:
    end_time = int(trace["end_time_ps"])
    label_w = 118
    plot_x = x + label_w
    plot_w = w - label_w - 8
    row_h = h / len(signal_names)

    for tick in range(5):
        tx = plot_x + plot_w * tick / 4
        lines.append(f'<line x1="{tx}" y1="{y}" x2="{tx}" y2="{y+h}" stroke="#d0d5dd" stroke-width="1"/>')
        lines.append(text(tx, y + h + 22, f"{end_time * tick / 4 / 1000:.0f}", 12, 400, "middle", "#667085"))
    lines.append(text(plot_x + plot_w / 2, y + h + 42, "time (ns)", 12, 500, "middle", "#667085"))

    for row, (signal, label) in enumerate(signal_names):
        top = y + row * row_h
        low = top + row_h * 0.72
        high = top + row_h * 0.28
        mid = (low + high) / 2
        if row % 2 == 0:
            lines.append(f'<rect x="{x}" y="{top}" width="{w}" height="{row_h}" fill="#f8fafc"/>')
        lines.append(text(x + label_w - 10, top + row_h * 0.62, label, 13, 600, "end", "#344054"))
        transitions = trace["signals"][signal]["transitions"]
        current_value = transitions[0][1] if transitions else "x"
        current_y = high if current_value == "1" else low if current_value == "0" else mid
        points = [(plot_x, current_y)]
        for transition_time, value in transitions[1:]:
            px = plot_x + plot_w * int(transition_time) / end_time
            next_y = high if value == "1" else low if value == "0" else mid
            points.extend([(px, current_y), (px, next_y)])
            current_y = next_y
        points.append((plot_x + plot_w, current_y))
        point_text = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
        lines.append(
            f'<polyline points="{point_text}" fill="none" stroke="#2563a8" '
            'stroke-width="2" stroke-linejoin="miter"/>'
        )


def generate_equivalence_figure(cpp: dict, python_pred: int, python_mem: int) -> None:
    s = canvas(
        1600,
        680,
        "다층 디지털 등가성 검증 결과",
        "Locked Python integer reference and independent Exact C++ checks converge on the same RTL XSim implementation",
    )
    s.append('<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#475467"/></marker></defs>')
    s.append(text(800, 82, "최종 출력만이 아니라 고정폭 연산 → 내부 상태 → Snapshot → 최종 상태까지 단계별 비교", 16, 500, "middle", "#475467"))

    box(s, 55, 130, 350, 190, "2-1  Python 정수 기준", [f"Prediction  {python_pred}/36", f"Final Membrane  {python_mem}/144", "mismatch = 0"], "#eff6ff", "#2563a8")
    box(s, 55, 385, 350, 190, "2-2  Exact C++ 기준", ["독립 handwritten 구현", "고정폭·내부 상태 추적", "RTL/XSim과 단계별 비교"], "#f5f3ff", "#6941c6")
    box(s, 625, 205, 350, 300, "Locked RTL / XSim", ["동일 12-bit 입력", "동일 1 kSPS cadence", "동일 60 s Snapshot", "동일 30-Snapshot final state", "PASS"], "#fff7e6", "#b7791f")
    arrow(s, 405, 225, 625, 285)
    arrow(s, 405, 480, 625, 425)

    exact_items = [
        ("고정폭 primitive", f"{cpp['fixed_width_checks']:,}/{cpp['fixed_width_checks']:,}"),
        ("Module microtrace", cpp["module_microtraces"]),
        ("Accepted-sample state", cpp["accepted_sample_state_hashes"]),
        ("Snapshot boundary", cpp["snapshot_boundaries"]),
        ("Final prediction", cpp["final_predictions"]),
        ("Final membranes", cpp["final_membranes"]),
    ]
    for i, (label, value) in enumerate(exact_items):
        col, row = i % 2, i // 2
        x, y = 1085 + col * 235, 135 + row * 150
        box(s, x, y, 205, 112, label, [value, "PASS"], "#ecfdf3", "#2f855a")
    arrow(s, 975, 355, 1085, 355)
    s.append(text(800, 630, "결론: Python 최종 출력과 Exact C++ 내부 상태 검증이 모두 locked RTL/XSim에 대해 불일치 0건", 17, 700, "middle", "#067647"))
    s.append("</svg>")
    (FIGURES / "VAL-02A_multilevel_digital_equivalence.svg").write_text("\n".join(s) + "\n", encoding="utf-8")


def generate_fulltop_figure(fulltop: list[dict[str, str]]) -> None:
    accepted = int(fulltop[0]["prof_accepted_samples"])
    windows = int(fulltop[0]["prof_windows"])
    decisions = int(fulltop[0]["prof_decisions"])
    total_cycles = int(fulltop[0]["prof_total_cycles"])
    window_latency = int(fulltop[0]["prof_last_window_latency"])

    s = canvas(
        1600,
        600,
        "Full-top 제어 흐름 검증 결과",
        "Counter-derived full-top XSim sequence for 36 complete 30-minute cases",
    )
    s.append(text(800, 82, "36개 모든 case에서 동일한 sample → Snapshot → final decision 순서를 확인", 16, 500, "middle", "#475467"))
    x0, x1, y = 120, 1480, 260
    s.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#475467" stroke-width="4"/>')
    for idx in range(windows + 1):
        x = x0 + (x1 - x0) * idx / windows
        s.append(f'<line x1="{x}" y1="{y-48}" x2="{x}" y2="{y+48}" stroke="#98a2b3" stroke-width="1"/>')
        if idx in {0, 1, 2, windows - 1, windows}:
            label = "START" if idx == 0 else "FINAL" if idx == windows else f"S{idx}"
            s.append(text(x, y - 62, label, 13, 700, "middle", "#344054"))
    s.append(text((x0 + x1) / 2, y - 62, "… 60,000 accepted samples per Snapshot × 30 …", 17, 700, "middle", "#344054"))
    s.append('<circle cx="120" cy="260" r="8" fill="#2563a8"/>')
    s.append('<circle cx="1480" cy="260" r="10" fill="#12b76a"/>')

    metrics = [
        ("Accepted samples", f"{accepted:,} / case"),
        ("Snapshots", f"{windows} / case"),
        ("Final decisions", f"{decisions} / case"),
        ("Window latency", f"{window_latency:,} cycles"),
        ("Total", f"{total_cycles:,} cycles"),
    ]
    for i, (label, value) in enumerate(metrics):
        x = 80 + i * 300
        box(s, x, 365, 260, 115, label, [value], "#f8fafc", "#667085")
    s.append(text(800, 550, "final_valid 36/36 · sample/window/decision counter invariant 36/36 · 제어 오류 0건", 18, 700, "middle", "#067647"))
    s.append("</svg>")
    (FIGURES / "VAL-02B_fulltop_control_timeline.svg").write_text("\n".join(s) + "\n", encoding="utf-8")


def generate_axi_figure(accel: dict, feeder: dict) -> None:
    s = canvas(
        1600,
        760,
        "AXI-Lite / AXI-Stream IP 검증 파형",
        "Selected signal traces captured from actual Vivado 2020.2 XSim smoke-test VCD files",
    )
    s.append(text(800, 79, "실제 XSim VCD에서 추출한 handshake · backpressure · TLAST · done/IRQ 파형", 16, 500, "middle", "#475467"))
    s.append('<rect x="40" y="105" width="740" height="570" rx="8" fill="#ffffff" stroke="#98a2b3" stroke-width="1.5"/>')
    s.append('<rect x="820" y="105" width="740" height="570" rx="8" fill="#ffffff" stroke="#98a2b3" stroke-width="1.5"/>')
    s.append(text(410, 138, "Sample Feeder IP", 20, 700, "middle"))
    s.append(text(1190, 138, "SNN ECG Accelerator IP", 20, 700, "middle"))
    s.append(text(410, 162, "FEEDER_SMOKE_PASS · 665 ns", 14, 700, "middle", "#067647"))
    s.append(text(1190, 162, "AXI_SMOKE_PASS · 2,095 ns", 14, 700, "middle", "#067647"))
    binary_wave(
        s,
        feeder,
        [("awvalid", "AWVALID"), ("wvalid", "WVALID"), ("bvalid", "BVALID"),
         ("tvalid", "TVALID"), ("tready", "TREADY"), ("tlast", "TLAST")],
        55,
        185,
        705,
        385,
    )
    binary_wave(
        s,
        accel,
        [("start", "START"), ("run_active", "RUN"), ("tvalid", "TVALID"),
         ("tready", "TREADY"), ("tlast", "TLAST"), ("done", "DONE"), ("irq", "IRQ")],
        835,
        185,
        705,
        385,
    )
    s.append(text(410, 635, "3 samples retained under stall; 3 transfers; TLAST on final sample", 14, 600, "middle", "#344054"))
    s.append(text(1190, 635, "16-sample reduced smoke case; start → stream → done/result/IRQ → clear", 14, 600, "middle", "#344054"))
    s.append(text(800, 718, "범위: packaged IP protocol smoke test. Canonical 1,800,000-sample control은 VAL-02B의 36-case full-top regression으로 별도 검증.", 14, 500, "middle", "#475467"))
    s.append("</svg>")
    (FIGURES / "VAL-02C_axi_ip_protocol_waveform.svg").write_text("\n".join(s) + "\n", encoding="utf-8")


def generate_tables(cpp: dict, py_pred: int, py_mem: int, fulltop: list[dict[str, str]],
                    integration: list[dict[str, str]], hashes: list[dict[str, str]], axi: dict) -> None:
    digital = f"""# Section 4 digital verification summary

This table is the compact result source for items 2-1 through 2-4.  It reports implementation equivalence and control/interface behavior, not classification accuracy.

| Item | Scope and method | Result | Judgment | Primary evidence |
|---|---|---:|---|---|
| 2-1 Python integer reference vs RTL/XSim | Same locked 36-case inputs; compare final class and four Final Membranes | Prediction {py_pred}/36; membrane {py_mem}/144; mismatch 0 | PASS | `components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv` |
| 2-2 Exact C++ vs RTL/XSim internal state | Exhaustive fixed-width primitives, module microtraces, accepted-sample state hashes, Snapshot boundaries, final outputs | Fixed-width {cpp['fixed_width_checks']:,}/{cpp['fixed_width_checks']:,}; microtrace {cpp['module_microtraces']}; states {cpp['accepted_sample_state_hashes']}; Snapshot {cpp['snapshot_boundaries']}; prediction {cpp['final_predictions']}; membrane {cpp['final_membranes']} | PASS | `benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json` |
| 2-3 Full-top control flow | 36 complete XSim cases; verify `final_valid`, accepted samples, Snapshot count, and decision count | 36/36; 1,800,000 samples, 30 Snapshots, 1 decision per case; 5,401,260 profiled cycles | PASS | `components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv` |
| 2-4 AXI/IP packaging and interface | Rerun packaged accelerator and sample-feeder IP smoke tests in Vivado XSim 2020.2 | {len(axi['tests'])}/{len(axi['tests'])} testbenches PASS; AXI-Lite read/write, AW/W skew, stalled-read stability, AXI-Stream backpressure/TLAST, counters, error clear, done/IRQ | PASS | `validation/digital_section4/axi_ip/axi_ip_smoke_summary.json`; `validation/digital_section4/axi_ip/logs/*.log` |

Notes:

- Exact C++ is an independent handwritten cross-check.  The locked Python integer model and canonical full-top XSim remain the reference/implementation authority for the final design.
- The accelerator smoke test uses a reduced 16-sample, two-Snapshot configuration to exercise the interface quickly; the canonical 1,800,000-sample, 30-Snapshot control flow is covered by item 2-3.
- XSim elaboration retained five pre-existing locked-RTL warnings (four 4-bit-to-8-bit port-width warnings and one unconnected `strong_event` port).  Both testbenches completed with zero smoke-test failures; the warnings are preserved in the log rather than hidden.
"""
    (TABLES / "section4_digital_validation_summary.md").write_text(digital, encoding="utf-8")

    integ = f"""# Section 4 analog-digital integration verification summary

| Item | Verification boundary | Result | Judgment | Primary evidence |
|---|---|---:|---|---|
| 3-1 XMODEL stream handoff | Compare SHA-256 of each generated signed 12-bit, 1 kSPS, 30-minute stream against the canonical replay input | {sum(bool_true(row['match']) for row in hashes)}/{len(hashes)} identical | PASS | `components/afe_xmodel/docs/integration_latest/afe36_sha256_bitidentity.csv` |
| 3-2 XMODEL stream to Digital RTL/XSim | Drive each stream at `sample_gap_cycles=2`; verify accepted count, Snapshot count, and decision count | {len(integration)}/{len(integration)} cases: 1,800,000 accepted, 30 Snapshots, 1 decision | PASS | `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv` |
| 3-3 End-to-end final state | Compare reproduced class and four Final Membranes with the canonical digital result | Prediction {sum(bool_true(row['pred_match']) for row in integration)}/{len(integration)}; membrane {sum(bool_true(row['mem_match']) for row in integration)}/{len(integration)} | PASS | `components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv` |

Interpretation: the table proves that the same XMODEL-generated ADC bytes enter RTL and that the implemented digital chain reproduces the expected final state.  It does not by itself prove clinical label accuracy or physical PCB/silicon behavior.
"""
    (TABLES / "section4_integration_validation_summary.md").write_text(integ, encoding="utf-8")


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    python_rows = read_csv(ROOT / "components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv")
    assert len(python_rows) == 36
    python_pred = sum(row["python_pred_class"] == row["xsim_pred_class"] for row in python_rows)
    membrane_cols = ["NSR", "CHF", "ARR", "AF"]
    python_mem = sum(
        row[f"python_final_mem_{label}"] == row[f"xsim_final_mem_{label}"]
        for row in python_rows for label in membrane_cols
    )
    assert python_pred == 36 and python_mem == 144

    cpp = json.loads((ROOT / "benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json").read_text(encoding="utf-8"))
    assert cpp["status"] == "pass"

    fulltop = read_csv(ROOT / "components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv")
    assert len(fulltop) == 36
    invariants = {
        "final_valid": "1",
        "prof_accepted_samples": "1800000",
        "prof_windows": "30",
        "prof_decisions": "1",
        "prof_total_cycles": "5401260",
    }
    assert all(all(row[key] == value for key, value in invariants.items()) for row in fulltop)

    integration = read_csv(ROOT / "components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv")
    hashes = read_csv(ROOT / "components/afe_xmodel/docs/integration_latest/afe36_sha256_bitidentity.csv")
    assert len(integration) == len(hashes) == 36
    assert all(bool_true(row["pred_match"]) and bool_true(row["mem_match"]) and bool_true(row["input_sha256_match"]) for row in integration)
    assert all(row["sample_gap_cycles"] == "2" and row["accepted_samples"] == "1800000" and row["windows"] == "30" and row["decisions"] == "1" for row in integration)
    assert all(bool_true(row["match"]) for row in hashes)

    axi = json.loads((VALIDATION / "axi_ip/axi_ip_smoke_summary.json").read_text(encoding="utf-8-sig"))
    assert axi["status"] == "PASS" and len(axi["tests"]) == 2
    assert all(test["status"] == "PASS" for test in axi["tests"])
    accel_trace = json.loads((VALIDATION / "axi_ip/traces/accelerator_smoke.selected_trace.json").read_text(encoding="utf-8"))
    feeder_trace = json.loads((VALIDATION / "axi_ip/traces/sample_feeder_smoke.selected_trace.json").read_text(encoding="utf-8"))

    generate_equivalence_figure(cpp, python_pred, python_mem)
    generate_fulltop_figure(fulltop)
    generate_axi_figure(accel_trace, feeder_trace)
    generate_tables(cpp, python_pred, python_mem, fulltop, integration, hashes, axi)
    print("generated 3 Section 4 SVG figures and 2 summary tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
