#!/usr/bin/env python3
"""Generate verified, non-benchmark SVG figures and their provenance index."""

from __future__ import annotations

import html
import json
from pathlib import Path
import shutil

from generate_section4_validation_artifacts import main as generate_section4_validation_artifacts


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "final"
SRC = ROOT / "figures" / "source"
APPROVED_SVG = SRC / "approved_svg"
DIGITAL = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
XMODEL = "4756a5086023547328ef44fd5fd87da3c250dc39"
MATLAB = "907f7e1f081a9d6a5703a32095d962143315a192"
LTSPICE = "INTEGRATED_LTSPICE_2026-07-19"


def esc(value) -> str:
    return html.escape(str(value))


def canvas(title: str, subtitle: str = "") -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">',
        '<rect width="1200" height="675" fill="#f7f9fc"/>',
        '<rect x="0" y="0" width="1200" height="92" fill="#102a43"/>',
        f'<text x="54" y="52" font-family="Arial, Noto Sans KR, sans-serif" font-size="30" font-weight="700" fill="white">{esc(title)}</text>',
        f'<text x="54" y="78" font-family="Arial, Noto Sans KR, sans-serif" font-size="14" fill="#bcccdc">{esc(subtitle)}</text>',
    ]


def txt(x, y, value, size=18, color="#102a43", weight=400, anchor="start") -> str:
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, Noto Sans KR, sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{esc(value)}</text>'


def box(x, y, w, h, title, lines=(), fill="#e8f1fb", stroke="#486581") -> list[str]:
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2"/>', txt(x+w/2, y+34, title, 19, "#102a43", 700, "middle")]
    for i, line in enumerate(lines):
        out.append(txt(x+w/2, y+64+i*25, line, 15, "#334e68", 400, "middle"))
    return out


def arrow(x1, y1, x2, y2, color="#486581") -> list[str]:
    return [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="4"/>', f'<polygon points="{x2},{y2} {x2-14},{y2-8} {x2-14},{y2+8}" fill="{color}"/>']


def footer(lines: list[str], note: str) -> None:
    lines.append('<rect x="40" y="625" width="1120" height="32" rx="8" fill="#e1e8f0"/>')
    lines.append(txt(600, 647, note, 13, "#486581", 400, "middle"))
    lines.append('</svg>')


def bar(lines, x, y, width, value, label, color="#2f80ed"):
    lines.append(txt(x, y-8, label, 16, "#243b53", 600))
    lines.append(f'<rect x="{x}" y="{y}" width="{width}" height="30" rx="6" fill="#d9e2ec"/>')
    lines.append(f'<rect x="{x}" y="{y}" width="{width*value/100:.1f}" height="30" rx="6" fill="{color}"/>')
    lines.append(txt(x+width+18, y+22, f"{value:.2f}%", 16, "#102a43", 700))


def write_svg(name: str, lines: list[str]) -> None:
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def install_approved_svg(name: str) -> None:
    """Install a user-approved editable SVG master without rasterization."""
    master = APPROVED_SVG / name
    if not master.is_file():
        raise FileNotFoundError(f"approved SVG master is missing: {master}")
    shutil.copyfile(master, OUT / name)


def paper_canvas(width: int, height: int, description: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{esc(description)}">',
        '<defs><marker id="paper-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#364152"/></marker></defs>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]


def paper_box(x, y, w, h, title, fill="#ffffff", stroke="#667085", stroke_width=2) -> list[str]:
    title_lines = [title] if isinstance(title, str) else list(title)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>']
    start_y = y + h / 2 - (len(title_lines) - 1) * 13 + 7
    for i, line in enumerate(title_lines):
        out.append(txt(x + w / 2, start_y + i * 26, line, 18, "#182230", 700, "middle"))
    return out


def paper_path(points, arrow=True, dashed=False, color="#364152", width=2.5) -> list[str]:
    point_text = " ".join(f"{x},{y}" for x, y in points)
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    marker = ' marker-end="url(#paper-arrow)"' if arrow else ""
    return [f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{dash}{marker}/>' ]


def paper_dot(x, y, color="#364152", r=5) -> str:
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    SRC.mkdir(parents=True, exist_ok=True)
    gm = json.loads((ROOT / "source_of_truth" / "global_metrics.yaml").read_text(encoding="utf-8"))
    m = gm["metrics"]
    data = {
        "classification": {
            "final_chunk_accuracy_percent": m["final_test_chunk_accuracy"]["value"],
            "final_record_majority_accuracy_percent": m["final_test_record_majority_accuracy"]["value"],
            "validation_model_selection_percent": m["validation_accuracy"]["value"],
        },
        "hardware": {
            "pure_rtl_lut": m["pure_rtl_lut"]["value"],
            "pure_rtl_ff": m["pure_rtl_ff"]["value"],
            "pure_rtl_bram": m["pure_rtl_bram"]["value"],
            "pure_rtl_dsp": m["pure_rtl_dsp"]["value"],
            "pure_rtl_wns_ns": m["pure_rtl_wns"]["value"],
        },
        "integration": {
            "input_sha256": m["afe_input_sha256_identity"]["value"],
            "afe_rtl_pred": m["afe_to_rtl_final_pred_equivalence"]["value"],
            "afe_rtl_mem": m["afe_to_rtl_final_mem_equivalence"]["value"],
            "board_pred": m["board_final_pred_equivalence"]["value"],
            "board_mem": m["board_final_mem_equivalence"]["value"],
            "canonical_sample_gap_cycles": m["canonical_sample_gap_cycles"]["value"],
        },
        "matlab": {"clipping_percent": m["matlab_representative_clipping_ratio"]["value"], "minimum_headroom_v": m["matlab_minimum_representative_headroom"]["value"]},
        "xmodel": {"mean_rms_lsb": m["xmodel_emulator_mean_rms"]["value"]},
        "afe": {
            "hpf_r_ohm": 10_000_000,
            "hpf_c_f": 33e-9,
            "hpf_fc_hz": 0.482287706339,
            "ia_rfb_ohm": 100_000,
            "ia_rg_ohm": 1_000,
            "ia_gain": 201,
            "notch_r_ohm": 26_526,
            "notch_c_f": 100e-9,
            "notch_bootstrap_k": 0.95,
            "notch_q": 5,
            "lpf_r_ohm": 1_000,
            "lpf_c_f": 1.06e-6,
            "lpf_fc_hz": 150.146172728,
            "adc_bits": 12,
            "adc_fs_hz": 1_000,
            "adc_vref_n": -1.65,
            "adc_vref_p": 1.65,
            "adc_lsb_v": 0.000805860805861,
            "source": "MATLAB parameter reference and fixed XMODEL RTL",
        },
        "streaming_memory": {
            "raw_window_samples": 1800000,
            "sample_width_bits": 12,
            "avoided_raw_window_bits": 21600000,
            "avoided_raw_window_bytes": 2700000,
            "claim_id": "CLM-023",
        },
        "architecture": {
            "sample_period_ms": 1,
            "snapshot_samples": 60000,
            "snapshots_per_decision": 30,
            "qrs_maf_pre_samples": 120,
            "qrs_maf_post_samples": 100,
            "rhythm_path": ["인접 표본값 차이", "QRS 막전위·불응기", "RR 틱 계수", "PNN 예측 일치", "RDM 연속 변화", "early-late 쌍"],
            "morphology_path": ["필터 기울기·이전 부호", "박동 구간 최대 진폭 코드", "QRS 폭·복잡도·에너지·선행 활동", "말단 구간 반복 지연"],
            "evidence_commit": DIGITAL,
        },
        "figure_layout": {
            "approved_svg_master": {
                "FIG-12": "figures/source/approved_svg/FIG-12_digital_processing_flow.svg",
                "FIG-15": "figures/source/approved_svg/FIG-15_afe_adc_signal_flow.svg",
                "regeneration": "copy byte-for-byte to figures/final",
            },
            "workflow": {
                "main_center_x": 550,
                "main_block_width": 600,
                "locked_test_source": "Record-wise Train / Validation / Locked Test Split",
                "locked_test_target": "Locked Final Test",
                "post_lock_retuning": False,
            },
            "digital": {
                "parallel_morphology_blocks": ["DSCR", "RAM", "QRS MAF", "RBBB-like"],
                "rhythm_morphology_merge": "Feature Accumulation & Class Scoring",
                "conceptual_grouping": True,
            },
            "analog": {
                "input_disturbance_targets": ["ECG+", "ECG−"],
                "rc_mismatch_targets": ["3-op-amp IA", "Active Twin-T 60 Hz Notch"],
                "op_amp_gbw_targets": ["3-op-amp IA", "Active Twin-T 60 Hz Notch", "150 Hz LPF + Buffer"],
                "vos_stress_target": "IA input pair",
                "adc_non_ideality_target": "ADC output code boundary",
            },
        },
        "benchmark_status": gm["benchmark"]["status"],
    }
    source_path = SRC / "figure_data.json"
    source_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    generate_section4_validation_artifacts()

    # FIG-01: motivation
    s = canvas("장시간 ECG 분류 문제", "짧은 박동 정보와 장시간 지속성을 함께 반영")
    s += box(70, 170, 270, 220, "표본값과 박동", ["기울기 · 박동 시점", "QRS · 최고점", "국소 사건 신호"])
    s += box(465, 170, 270, 220, "60초 Snapshot", ["리듬 + 파형 형태", "국소 클래스 증거", "30회 판독"])
    s += box(860, 170, 270, 220, "30분 최종 상태", ["부호 막전위", "장시간 지속성", "승자독식 클래스"])
    s += arrow(340, 280, 465, 280) + arrow(735, 280, 860, 280)
    s.append(txt(600, 500, "핵심: 빠르기 자체가 아니라 시간 계층을 streaming state로 구조화", 24, "#0b7285", 700, "middle"))
    footer(s, "설계 동기를 설명하는 그림이며 임상 진단을 뜻하지 않음")
    write_svg("FIG-01_long_window_motivation.svg", s)

    # FIG-02: user-approved research workflow, redrawn as a lossless vector.
    workflow_layout = data["figure_layout"]["workflow"]
    assert workflow_layout["main_center_x"] == 550
    assert workflow_layout["main_block_width"] == 600
    assert workflow_layout["locked_test_target"] == "Locked Final Test"
    assert workflow_layout["post_lock_retuning"] is False
    s = paper_canvas(1200, 1700, "Public ECG data are split record-wise; front-end and digital development use development data, the digital design is locked before one held-out final test, and implementation plus analog-digital integration verification lead to the final report")
    main_x, main_w, main_h, center_x = 250, workflow_layout["main_block_width"], 100, workflow_layout["main_center_x"]
    main_y = [30, 180, 330, 480, 880, 1030, 1180, 1330, 1480]
    s += paper_box(main_x, main_y[0], main_w, main_h, "Public ECG Data", "#eff6ff", "#2563a8")
    s += paper_box(main_x, main_y[1], main_w, main_h, ["Record-wise Train / Validation /", "Locked Test Split"], "#eff6ff", "#2563a8")
    s += paper_path([(center_x, 130), (center_x, 180)])
    s += paper_box(main_x, main_y[2], main_w, main_h, ["Front End Verification", "(MATLAB, LTspice, XMODEL)"], "#eff6ff", "#2563a8")
    s += paper_path([(center_x, 280), (center_x, 330)])
    s += paper_box(main_x, main_y[3], main_w, main_h, "Digital Model / RTL Development", "#ecfdf3", "#2f855a")
    s += paper_path([(center_x, 430), (center_x, 480)])

    s += paper_box(920, 330, 250, 100, ["Locked Test Data", "(Held-out)"], "#fef3c7", "#b7791f")
    s += paper_path([(850, 230), (1045, 230), (1045, 330)])

    s += paper_path([(center_x, 580), (center_x, 630)])
    s.append('<polygon points="550,630 790,730 550,830 310,730" fill="#ecfdf3" stroke="#2f855a" stroke-width="2.5"/>')
    s.append(txt(center_x, 723, "Digital Validation", 20, "#182230", 700, "middle"))
    s.append(txt(center_x, 751, "Criteria Met?", 20, "#182230", 700, "middle"))
    s += paper_path([(310, 730), (120, 730), (120, 530), (250, 530)])
    s.append(txt(150, 715, "No", 17, "#182230", 700))

    s += paper_box(main_x, main_y[4], main_w, main_h, "Design Lock", "#eff6ff", "#2563a8")
    s += paper_path([(center_x, 830), (center_x, 880)])
    s.append(txt(580, 860, "Yes", 17, "#182230", 700))
    s += paper_box(main_x, main_y[5], main_w, main_h, ["Locked Final Test", "(Used Once Only)"], "#fef3c7", "#b7791f")
    s += paper_path([(center_x, 980), (center_x, 1030)])
    s += paper_path([(1045, 430), (1045, 1080), (850, 1080)])

    s += paper_box(main_x, main_y[6], main_w, main_h, ["Implementation Verification", "(RTL / IP / FPGA)"], "#f5f3ff", "#6b46c1")
    s += paper_path([(center_x, 1130), (center_x, 1180)])
    s += paper_box(main_x, main_y[7], main_w, main_h, ["Analog-Digital Integration Verification", "(XMODEL – RTL End-to-End)"], "#eff6ff", "#2563a8")
    s += paper_path([(center_x, 1280), (center_x, 1330)])
    s += paper_box(main_x, main_y[8], main_w, main_h, "Final Results & Report", "#eff6ff", "#2563a8")
    s += paper_path([(center_x, 1430), (center_x, 1480)])
    s.append('</svg>')
    write_svg("FIG-02_research_workflow.svg", s)

    # FIG-03 ownership
    s = canvas("Contributor ownership and handoff", "구현 owner·verification owner·integration owner를 분리")
    s += box(70, 150, 300, 310, "서민우 · MATLAB", ["nominal AFE/ADC", "headroom/clipping", "signed vectors", "manifest/hash"], fill="#fff4e6")
    s += box(450, 150, 300, 310, "이수환 · XMODEL", ["non-ideal/stress", "full-record AFE", "SHA256 handoff", "AFE→RTL compare"], fill="#e6fcf5")
    s += box(830, 150, 300, 310, "양건 · Digital/Lead", ["architecture/evaluation", "RTL/Vivado/IP-XACT", "Vitis/board", "final integration"], fill="#e7f5ff")
    s += arrow(370, 305, 450, 305) + arrow(750, 305, 830, 305)
    footer(s, "Collaborative chain does not transfer one contributor's implementation ownership to another")
    write_svg("FIG-03_ownership_handoff.svg", s)

    # FIG-04 analog verification flow
    s = paper_canvas(
        1500,
        440,
        "MATLAB to LTspice frequency-response verification followed by LTspice to XMODEL ADC-output verification",
    )
    s.append('<title>아날로그 검증 흐름</title>')
    s.append('<desc>MATLAB과 LTspice의 주파수 응답을 비교한 뒤 LTspice와 XMODEL의 ADC 출력을 비교하는 검증 순서</desc>')
    s.append(txt(750, 58, "아날로그 검증 흐름", 27, "#182230", 700, "middle"))
    s += paper_box(65, 165, 270, 130, ["MATLAB", "사전 설계 모델"], "#eff6ff", "#2563a8")
    s += paper_box(615, 165, 270, 130, ["LTspice", "회로 시뮬레이션"], "#fff7e6", "#b7791f")
    s += paper_box(1165, 165, 270, 130, ["XMODEL", "Verilog 행동모델"], "#ecfdf3", "#2f855a")
    s += paper_path([(335, 230), (615, 230)])
    s += paper_path([(885, 230), (1165, 230)])
    s.append(txt(475, 112, "주파수 응답 비교", 18, "#182230", 700, "middle"))
    s.append(txt(475, 138, "Overall AFE · 60 Hz Notch", 15, "#475467", 400, "middle"))
    s.append(txt(1025, 112, "ADC 출력 비교", 18, "#182230", 700, "middle"))
    s.append(txt(1025, 138, "Waveform · Error Histogram", 15, "#475467", 400, "middle"))
    s.append('</svg>')
    write_svg("FIG-04_analog_validation_flow.svg", s)

    # VAL-02 digital verification flow
    s = paper_canvas(
        1500,
        520,
        "Digital verification flow from two software references through RTL XSim, full-top control, and AXI IP validation",
    )
    s.append('<title>디지털 회로 검증 흐름</title>')
    s.append('<desc>Python 최종 출력 기준과 Exact C++ 내부 상태 기준을 RTL XSim에 교차 비교하고 Full-top 제어와 AXI IP 인터페이스를 검증하는 순서</desc>')
    s.append(txt(750, 58, "디지털 회로 검증 흐름", 27, "#182230", 700, "middle"))
    s += paper_box(65, 125, 300, 120, ["Python 정수 기준", "최종 출력 기준"], "#eff6ff", "#2563a8")
    s += paper_box(65, 315, 300, 120, ["Exact C++", "고정폭·내부 상태 기준"], "#f4f3ff", "#6941c6")
    s += paper_box(500, 220, 300, 120, ["RTL / XSim", "Core"], "#fff7e6", "#b7791f")
    s += paper_box(890, 220, 260, 120, ["Full-top RTL", "표본→Snapshot→판정"], "#fef3f2", "#b42318")
    s += paper_box(1210, 220, 240, 120, ["AXI / IP", "Lite · Stream"], "#ecfdf3", "#2f855a")
    s += paper_path([(365, 185), (430, 185), (430, 250), (500, 250)])
    s += paper_path([(365, 375), (430, 375), (430, 310), (500, 310)])
    s += paper_path([(800, 280), (890, 280)])
    s += paper_path([(1150, 280), (1210, 280)])
    s.append(txt(430, 155, "최종 출력 비교", 16, "#475467", 700, "middle"))
    s.append(txt(430, 415, "내부 상태 비교", 16, "#475467", 700, "middle"))
    s.append(txt(845, 205, "제어 흐름 검증", 16, "#475467", 700, "middle"))
    s.append(txt(1180, 205, "인터페이스 검증", 16, "#475467", 700, "middle"))
    s.append('</svg>')
    write_svg("VAL-02_digital_validation_flow.svg", s)

    # VAL-03 analog-digital integration verification flow
    s = paper_canvas(
        1500,
        440,
        "Analog-digital integration verification from XMODEL AFE ADC output through signed stream handoff to Digital RTL XSim",
    )
    s.append('<title>아날로그–디지털 통합 검증 흐름</title>')
    s.append('<desc>XMODEL AFE ADC 출력의 signed 12-bit 인계와 Digital RTL XSim의 End-to-End 결과를 검증하는 순서</desc>')
    s.append(txt(750, 58, "아날로그–디지털 통합 검증 흐름", 27, "#182230", 700, "middle"))
    s += paper_box(70, 165, 260, 130, ["XMODEL AFE·ADC", "ECG→ADC code"], "#eff6ff", "#2563a8")
    s += paper_box(440, 165, 260, 130, ["Signed 12-bit Stream", "30 min × 36 cases"], "#f4f3ff", "#6941c6")
    s += paper_box(810, 165, 260, 130, ["Digital RTL / XSim", "30 Snapshots"], "#fff7e6", "#b7791f")
    s += paper_box(1180, 165, 250, 130, ["End-to-End 비교", "통합 검증 통과"], "#ecfdf3", "#2f855a")
    s += paper_path([(330, 230), (440, 230)])
    s += paper_path([(700, 230), (810, 230)])
    s += paper_path([(1070, 230), (1180, 230)])
    s.append(txt(385, 138, "1 kSPS 인계", 16, "#475467", 700, "middle"))
    s.append(txt(755, 138, "SHA256 36/36", 16, "#475467", 700, "middle"))
    s.append(txt(1125, 138, "Pred · Mem 36/36", 16, "#475467", 700, "middle"))
    s.append('</svg>')
    write_svg("VAL-03_analog_digital_integration_flow.svg", s)

    # FIG-05 split
    s = canvas("Strict source-record-wise evaluation", "record leakage 방지와 database confounding은 서로 다른 문제")
    s += box(70, 160, 280, 260, "Source records", ["record_id is split unit", "all chunks stay together"])
    s += box(460, 130, 220, 120, "Train", ["61 / 68"] ,fill="#e6fcf5")
    s += box(460, 285, 220, 120, "Validation", ["32 / 32", "selection only"], fill="#fff9db")
    s += box(800, 210, 300, 170, "Locked final-test", ["29 / 36 chunks", "one evaluation", "not used for selection"], fill="#e7f5ff")
    s += arrow(350, 290, 460, 190) + arrow(350, 290, 460, 345) + arrow(680, 345, 800, 295)
    footer(s, "Prevents direct record leakage; does not eliminate database-to-class confounding")
    write_svg("FIG-05_strict_recordwise_protocol.svg", s)

    # FIG-06 MATLAB
    s = canvas("MATLAB nominal pre-validation summary", "대표 NSR/CHF/ARR/AF 60초 record")
    s += box(80, 170, 430, 260, "Representative clipping", [f"{data['matlab']['clipping_percent']:.1f}%", "4 / 4 classes", "no rail hits"], fill="#e6fcf5")
    s += box(690, 170, 430, 260, "Minimum rail headroom", [f"{data['matlab']['minimum_headroom_v']:.4f} V", "minimum across 4 records", "nominal MATLAB model"], fill="#e7f5ff")
    footer(s, "Selected nominal records only; not physical AFE/ADC measurement")
    write_svg("FIG-06_matlab_nominal_summary.svg", s)

    # FIG-07 XMODEL
    s = canvas("XMODEL verification scope", "model-based waveform, stress, and handoff evidence")
    labels = [(70,150,"Waveform match",[f"mean RMS {data['xmodel']['mean_rms_lsb']:.2f} LSB","36 segments · lag 0"]),(440,150,"Stress scope",["PLI · offset/wander","R/C · GBW/VOS · ADC"]),(810,150,"Integration",["input SHA 36/36","gap=2 pred/mem 36/36"])]
    for x,y,t,l in labels: s += box(x,y,320,290,t,l,fill="#edf2ff")
    footer(s, "Not transistor-level, post-layout, PCB, ADC-silicon, or clinical validation")
    write_svg("FIG-07_xmodel_scope.svg", s)

    # FIG-08 handoff
    s = canvas("기능 등가성", "같은 입력 byte → 같은 표본 간격 → 같은 디지털 상태")
    s += box(65, 170, 280, 240, "AFE 생성 구간", ["signed 12-bit", "1,800,000표본"])
    s += box(460, 170, 280, 240, "SHA256 동일성", [data['integration']['input_sha256'], "모든 byte 일치"] ,fill="#e6fcf5")
    s += box(855, 170, 280, 240, "고정 RTL", ["sample_gap_cycles=2", "예측 36/36", "막전위 36/36"], fill="#e7f5ff")
    s += arrow(345, 290, 460, 290) + arrow(740, 290, 855, 290)
    footer(s, "입출력 동일성은 통합 증거이며 정답 표지 100%를 뜻하지 않음")
    write_svg("FIG-08_signed_stream_handoff.svg", s)

    # FIG-09 hierarchy
    s = canvas("Digital validation hierarchy", "reference → RTL → implementation → packaged system → board")
    levels = [(70,470,1060,"FPGA board replay · pred/mem 36/36","#d0ebff"),(145,380,910,"Vitis/MicroBlaze + packaged IP","#d3f9d8"),(220,290,760,"Vivado implementation · positive WNS","#fff3bf"),(295,200,610,"Full-top RTL/XSim · mismatch 0/36","#ffe8cc"),(370,110,460,"Locked integer reference","#e5dbff")]
    for x,y,w,label,color in levels:
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="62" rx="10" fill="{color}" stroke="#486581"/>')
        s.append(txt(600,y+40,label,18,"#102a43",700,"middle"))
    footer(s, "Each layer proves implementation reproduction; label correctness remains a separate metric")
    write_svg("FIG-09_digital_validation_hierarchy.svg", s)

    # FIG-10 classification
    s = canvas("분류 결과", "검증 결과는 모델 선택용으로 분리하고 최종 시험을 중심에 표시")
    bar(s, 150, 190, 720, data['classification']['final_chunk_accuracy_percent'], "최종 시험 30분 구간", "#2f80ed")
    bar(s, 150, 300, 720, data['classification']['final_record_majority_accuracy_percent'], "최종 record-majority", "#12b886")
    bar(s, 150, 410, 720, data['classification']['validation_model_selection_percent'], "검증 결과(모델 선택 전용)", "#adb5bd")
    s.append(txt(600, 545, "주 결과: 29/36 = 80.56%", 26, "#102a43", 700, "middle"))
    footer(s, "공개 데이터셋 공학 결과이며 데이터베이스와 클래스의 결합이 남음")
    write_svg("FIG-10_classification_summary.svg", s)

    # FIG-11 confounding
    s = canvas("Database–class confounding and claim boundary", "record-wise split solves one risk, not every domain risk")
    s += box(65, 150, 300, 300, "What is controlled", ["source-record leakage", "same stream contract", "no filename/DB feature", "locked final-test"] ,fill="#e6fcf5")
    s += box(450, 150, 300, 300, "What remains", ["DB ↔ class coupling", "acquisition/lead/noise", "domain signatures", "clinical generalization"] ,fill="#fff4e6")
    s += box(835, 150, 300, 300, "What still holds", ["RTL correctness", "bit-exact equivalence", "IP packaging", "board replay/resources"] ,fill="#e7f5ff")
    footer(s, "Future: same-acquisition multi-class cohort or explicit cross-domain protocol")
    write_svg("FIG-11_confounding_claim_boundary.svg", s)

    # FIG-12: user-approved digital flow, redrawn as a lossless vector.
    digital_layout = data["figure_layout"]["digital"]
    morphology_labels = digital_layout["parallel_morphology_blocks"]
    assert morphology_labels == ["DSCR", "RAM", "QRS MAF", "RBBB-like"]
    assert digital_layout["conceptual_grouping"] is True
    s = paper_canvas(1700, 720, "Signed ECG passes through delta calculation, Strong-Event detection and a QRS LIF neuron; rhythm and morphology evidence merge at class scoring before Snapshot and Final Membrane accumulation")
    s += paper_box(20, 270, 130, 90, "Signed ECG", "#eff6ff", "#2563a8")
    s += paper_box(190, 270, 150, 90, ["ΔECG", "Calculation"], "#ecfdf3", "#2f855a")
    s += paper_box(380, 270, 170, 90, ["Strong-Event", "Detector"], "#ecfdf3", "#2f855a")
    s += paper_box(590, 270, 140, 90, ["QRS LIF", "Neuron"], "#fffbeb", "#b7791f")
    s += paper_path([(150, 315), (190, 315)])
    s += paper_path([(340, 315), (380, 315)])
    s += paper_path([(550, 315), (590, 315)])

    s.append(txt(930, 38, "Rhythm Feature Path", 19, "#182230", 700, "middle"))
    s.append('<line x1="760" y1="52" x2="1100" y2="52" stroke="#364152" stroke-width="1.5"/>')
    s += paper_box(780, 75, 150, 85, "RR Counter", "#ecfeff", "#0e7490")
    s += paper_box(970, 75, 190, 85, ["PNN / RDM /", "Ectopic Evidence"], "#ecfeff", "#0e7490")
    s += paper_path([(660, 270), (660, 117), (780, 117)])
    s += paper_path([(930, 117), (970, 117)])

    s.append(txt(820, 405, "Morphology Feature Path", 19, "#182230", 700, "middle"))
    s.append('<line x1="620" y1="419" x2="1020" y2="419" stroke="#364152" stroke-width="1.5"/>')

    # Strong-Event and QRS evidence enter one reader-facing morphology bus.
    # The four feature blocks are independent peers; there are no inter-block
    # arrows and no implication of literal post-synthesis netlist connectivity.
    s += paper_path([(465, 360), (465, 440), (610, 440)], arrow=False)
    s += paper_path([(660, 360), (660, 440)], arrow=False)
    s += paper_path([(610, 440), (1110, 440)], arrow=False)
    s.append(paper_dot(610, 440, "#364152", 4))
    s.append(paper_dot(660, 440, "#364152", 4))

    morphology_x = [630, 770, 910, 1050]
    morphology_centers = [x + 60 for x in morphology_x]
    for x, center, label in zip(morphology_x, morphology_centers, morphology_labels):
        s += paper_path([(center, 440), (center, 480)])
        s += paper_box(x, 480, 120, 80, label, "#fff7ed", "#c05621")
        s += paper_path([(center, 560), (center, 610)])
    s += paper_path([(morphology_centers[0], 610), (1175, 610)], arrow=False)
    s.append(paper_dot(1175, 610, "#364152", 4))

    s += paper_box(1180, 245, 220, 140, ["Feature Accumulation", "& Class Scoring"], "#eef2ff", "#4f46e5")
    s += paper_path([(1160, 117), (1165, 117), (1165, 285), (1180, 285)])
    s += paper_path([(1175, 610), (1175, 345), (1180, 345)])
    s += paper_box(1430, 260, 190, 110, ["60 s Snapshot", "Membrane"], "#f5f3ff", "#6b46c1")
    s += paper_path([(1400, 315), (1430, 315)])
    s += paper_box(1450, 420, 150, 75, ["30-Snapshot", "Accumulation"], "#f5f3ff", "#6b46c1")
    s += paper_path([(1525, 370), (1525, 420)])
    s += paper_box(1430, 545, 190, 120, ["30 min Final", "Membrane"], "#fdf4ff", "#9c36b5")
    s += paper_path([(1525, 495), (1525, 545)])
    for y, label in [(565, "NSR"), (595, "CHF"), (625, "ARR"), (655, "AF")]:
        s += paper_path([(1620, y), (1645, y)], arrow=False)
        s.append(txt(1652, y + 6, label, 16, "#182230", 700))
    s.append('</svg>')
    # The editable Inkscape SVG is the approved source master. Keep the
    # programmatic construction above as a semantic layout reference, but
    # install the approved vector byte-for-byte so manual alignment survives.
    install_approved_svg("FIG-12_digital_processing_flow.svg")

    # FIG-15: user-approved AFE/ADC flow, redrawn as a lossless vector. Solid
    # arrows carry the signal; dashed arrows inject disturbances/non-idealities.
    analog_layout = data["figure_layout"]["analog"]
    assert analog_layout["input_disturbance_targets"] == ["ECG+", "ECG−"]
    assert analog_layout["rc_mismatch_targets"] == ["3-op-amp IA", "Active Twin-T 60 Hz Notch"]
    assert analog_layout["op_amp_gbw_targets"] == ["3-op-amp IA", "Active Twin-T 60 Hz Notch", "150 Hz LPF + Buffer"]
    assert analog_layout["adc_non_ideality_target"] == "ADC output code boundary"
    s = paper_canvas(1700, 700, "Differential ECG passes through paired HPFs, a 3-op-amp instrumentation amplifier, active 60 Hz notch, buffered 150 Hz low-pass filter, 12-bit ADC, and signed digital handoff; separate dashed paths identify the XMODEL stress sources")

    # Non-ideal model row.
    s += paper_box(65, 45, 300, 78, "Input Disturbance Injection", "#faf5ff", "#6b46c1")
    s += paper_box(500, 45, 255, 78, "R/C Mismatch Model", "#faf5ff", "#6b46c1")
    s += paper_box(830, 45, 300, 78, "Op-Amp GBW / VOS Model", "#faf5ff", "#6b46c1")
    s += paper_box(1260, 45, 300, 78, "ADC Non-Ideality Injection", "#faf5ff", "#6b46c1")

    # Differential signal entry and paired high-pass filters.
    s.append(txt(30, 330, "ECG+", 18, "#182230", 700))
    s.append(txt(30, 470, "ECG−", 18, "#182230", 700))
    s.append(paper_dot(125, 323, "#2563a8", 7))
    s.append(paper_dot(125, 463, "#2563a8", 7))
    s += paper_path([(132, 323), (200, 323)])
    s += paper_path([(132, 463), (200, 463)])
    s += paper_box(200, 270, 165, 106, "HPF (+)", "#ecfdf3", "#2f855a")
    s += paper_box(200, 410, 165, 106, "HPF (−)", "#ecfdf3", "#2f855a")

    # Paired HPF outputs merge at the instrumentation amplifier.
    s.append('<polygon points="450,245 450,540 635,393" fill="#ecfdf3" stroke="#2f855a" stroke-width="2.5"/>')
    s.append(txt(515, 382, "3-op-amp", 18, "#182230", 700, "middle"))
    s.append(txt(515, 409, "IA", 18, "#182230", 700, "middle"))
    s += paper_path([(365, 323), (450, 323)])
    s += paper_path([(365, 463), (450, 463)])

    # Main AFE/ADC signal chain.
    s += paper_box(685, 333, 190, 120, ("Active Twin-T", "60 Hz Notch"), "#fff7ed", "#c05621")
    s += paper_box(925, 333, 210, 120, ("150 Hz LPF", "+ Buffer"), "#fff7ed", "#c05621")
    s += paper_box(1185, 333, 150, 120, "12-bit ADC", "#f5f3ff", "#6b46c1")
    s += paper_box(1385, 333, 175, 120, ("Signed 12-bit", "Stream"), "#f5f3ff", "#6b46c1")
    s += paper_path([(635, 393), (685, 393)])
    s += paper_path([(875, 393), (925, 393)])
    s += paper_path([(1135, 393), (1185, 393)])
    s += paper_path([(1335, 393), (1360, 393)], arrow=False)
    s.append(paper_dot(1360, 393, "#364152", 5))
    s += paper_path([(1360, 393), (1385, 393)])
    s += paper_path([(1560, 393), (1615, 393)])
    s.append(txt(1622, 400, "Digital", 17, "#182230", 700))
    s.append(txt(1622, 423, "RTL", 17, "#182230", 700))

    # Dashed model-injection paths are kept visually separate from signal flow.
    s += paper_path([(215, 123), (215, 185), (125, 185), (125, 316)], dashed=True, color="#6b46c1")
    s += paper_path([(215, 185), (95, 185), (95, 463), (118, 463)], dashed=True, color="#6b46c1")
    s += paper_path([(628, 123), (628, 170), (540, 170), (540, 238)], dashed=True, color="#6b46c1")
    s += paper_path([(628, 170), (780, 170), (780, 326)], dashed=True, color="#6b46c1")
    s += paper_path([(980, 45), (980, 20), (420, 20), (420, 245), (443, 245)], dashed=True, color="#6b46c1")
    s += paper_path([(980, 123), (980, 205), (810, 205), (810, 326)], dashed=True, color="#6b46c1")
    s += paper_path([(980, 205), (1030, 205), (1030, 326)], dashed=True, color="#6b46c1")
    s += paper_path([(1410, 123), (1410, 245), (1360, 245), (1360, 386)], dashed=True, color="#6b46c1")

    s.append(txt(850, 625, "Solid arrows: signal path / Dashed arrows: injected disturbance or non-ideal model", 17, "#344054", 600, "middle"))
    s.append('</svg>')
    install_approved_svg("FIG-15_afe_adc_signal_flow.svg")

    # Preserve the seven fixed MATLAB figures byte-for-byte in the integrated
    # figure package. Their captions and limitations remain owned by MATLAB.
    matlab_figure_root = ROOT / "components" / "matlab_prevalidation" / "matlab_afe_validation" / "figures"
    inherited_matlab_figures = [
        ("MAT-01", "fig_afe_chain_overview.png", "MAT-01_afe_chain_overview.png", "MATLAB nominal AFE+ADC chain overview"),
        ("MAT-02", "fig_total_frequency_response.png", "MAT-02_total_frequency_response.png", "MATLAB nominal total frequency-response reference"),
        ("MAT-03", "fig_notch_dense_sweep.png", "MAT-03_notch_dense_sweep.png", "Active Twin-T dense 60 Hz sweep"),
        ("MAT-04", "fig_dynamic_range_headroom.png", "MAT-04_dynamic_range_headroom.png", "Representative ADC rail headroom"),
        ("MAT-05", "fig_adc_code_distribution.png", "MAT-05_adc_code_distribution.png", "Representative offset-binary ADC-code distribution"),
        ("MAT-06", "fig_reference_vector_handoff.png", "MAT-06_reference_vector_handoff.png", "MATLAB reference-vector handoff"),
        ("MAT-07", "fig_matlab_prevalidation_flow.png", "MAT-07_prevalidation_flow.png", "MATLAB nominal pre-validation role"),
    ]
    for _, source_name, output_name, _ in inherited_matlab_figures:
        shutil.copyfile(matlab_figure_root / source_name, OUT / output_name)

    figures = [
        ("FIG-01", "figures/final/FIG-01_long_window_motivation.svg", "양건", ["docs/PROBLEM_DEFINITION_KR.md"], ["INTEGRATED"], "장시간 ECG에서 국소 evidence와 장기 persistence를 결합하는 문제 동기", "architectural motivation", "Holter-oriented; not clinical certification"),
        ("FIG-02", "figures/final/FIG-02_research_workflow.svg", "서민우·이수환·양건", ["source_of_truth/upstream_commits.yaml", "validation/afe_ltspice_xmodel_aligned/README.md", "components/digital_accelerator/configs/final_submission_locked_model.json", "components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv", "components/digital_accelerator/reports/final/final_metrics.json"], [MATLAB,LTSPICE,XMODEL,DIGITAL], "Record-wise 분할 뒤 Train·Validation으로 MATLAB→LTspice→XMODEL Front End와 Digital RTL을 설계·검증하고, 설계 잠금 뒤 Held-out Test를 최초 1회 사용한 다음 구현·통합 등가성 검증으로 이어지는 전체 workflow", "data-separated portrait workflow with one pre-lock digital correction loop and a one-time locked final test", "the post-lock implementation and integration stages verify equivalence and do not permit model, threshold, or structural retuning"),
        ("FIG-03", "figures/final/FIG-03_ownership_handoff.svg", "양건(편집)", ["source_of_truth/ownership_matrix.csv"], [MATLAB,LTSPICE,XMODEL,DIGITAL], "Contributor ownership과 handoff", "ownership", "collaboration does not transfer implementation ownership"),
        ("FIG-04", "figures/final/FIG-04_analog_validation_flow.svg", "양건(통합 편집)", ["figures/final/SPICE-03_matlab_ltspice_afe_response.png", "figures/final/SPICE-04_matlab_ltspice_notch_response.png", "figures/final/SPICE-05_xmodel_ltspice_adc_waveform_full.png", "figures/final/SPICE-08_xmodel_ltspice_adc_error_histogram.png"], [MATLAB,LTSPICE,XMODEL,"INTEGRATED"], "MATLAB–LTspice 주파수 응답 비교와 LTspice–XMODEL ADC 출력 비교의 아날로그 검증 흐름", "two-stage analog model comparison", "model- and schematic-level simulation evidence; not physical PCB or silicon measurement"),
        ("VAL-02", "figures/final/VAL-02_digital_validation_flow.svg", "양건(통합 편집)", ["components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv", "benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json", "components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv", "validation/digital_section4/axi_ip/axi_ip_smoke_summary.json"], [DIGITAL,"46f90224fca0dea3a592049a5e14b97680d529e0","INTEGRATED"], "Python과 Exact C++ 기준을 RTL/XSim에 비교한 뒤 Full-top 제어와 AXI/IP 인터페이스로 확장하는 디지털 검증 흐름", "digital functional and interface verification sequence", "AXI/IP smoke tests are reduced protocol tests; canonical full-length control is verified separately"),
        ("VAL-02A", "figures/final/VAL-02A_multilevel_digital_equivalence.svg", "양건(통합 편집)", ["components/digital_accelerator/reports/final/xsim_locked_model_predictions.csv", "benchmarks/accelerator_benefit/results/post_benchmark_equivalence.json", "tools/generate_section4_validation_artifacts.py"], [DIGITAL,"46f90224fca0dea3a592049a5e14b97680d529e0","INTEGRATED"], "Python 최종 출력과 Exact C++ 내부 상태를 locked RTL/XSim에 단계별로 비교한 다층 등가성 검증 결과", "36 final outputs plus fixed-width, microtrace, accepted-sample state, and Snapshot-boundary checks", "Exact C++ is an independent cross-check; locked Python and canonical XSim remain the final reference and implementation authorities"),
        ("VAL-02B", "figures/final/VAL-02B_fulltop_control_timeline.svg", "양건(통합 편집)", ["components/digital_accelerator/reports/final/fulltop_xsim_final_test_36/locked_class_cases_fulltop_xsim_predictions.csv", "tools/generate_section4_validation_artifacts.py"], [DIGITAL,"INTEGRATED"], "36개 full-top XSim case의 counter에서 확인한 sample·Snapshot·final decision 제어 순서", "36 complete 1,800,000-sample cases, 30 Snapshots and one decision per case", "counter-derived control sequence, not a literal 5.4-million-cycle waveform screenshot"),
        ("VAL-02C", "figures/final/VAL-02C_axi_ip_protocol_waveform.svg", "양건(통합 편집)", ["validation/digital_section4/axi_ip/axi_ip_smoke_summary.json", "validation/digital_section4/axi_ip/traces/accelerator_smoke.selected_trace.json", "validation/digital_section4/axi_ip/traces/sample_feeder_smoke.selected_trace.json", "validation/digital_section4/axi_ip/logs/accelerator_smoke.log", "validation/digital_section4/axi_ip/logs/sample_feeder_smoke.log", "tools/generate_section4_validation_artifacts.py"], [DIGITAL,"INTEGRATED"], "Vivado XSim VCD에서 추출한 AXI-Lite·AXI-Stream handshake, backpressure, TLAST 및 done/IRQ 파형", "packaged accelerator and sample-feeder IP smoke tests in Vivado XSim 2020.2", "reduced 16-sample accelerator protocol test; canonical full-length control is covered by VAL-02B"),
        ("VAL-03", "figures/final/VAL-03_analog_digital_integration_flow.svg", "양건(통합 편집)", ["components/afe_xmodel/docs/integration_latest/afe36_sha256_bitidentity.csv", "components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv"], [XMODEL,DIGITAL,"INTEGRATED"], "XMODEL AFE·ADC의 signed 12-bit 출력이 Digital RTL/XSim 최종 상태까지 이어지는 아날로그–디지털 통합 검증 흐름", "36-case XMODEL-to-RTL handoff and end-to-end equivalence", "model-based AFE and RTL simulation evidence; not physical analog acquisition or clinical validation"),
        ("FIG-05", "figures/final/FIG-05_strict_recordwise_protocol.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Strict source-record-wise evaluation protocol", "evaluation protocol", "does not solve database-class confounding"),
        ("FIG-06", "figures/final/FIG-06_matlab_nominal_summary.svg", "서민우", ["components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv"], [MATLAB], "MATLAB representative nominal clipping/headroom", "four selected nominal 60-second records", "not physical measurement"),
        ("FIG-07", "figures/final/FIG-07_xmodel_scope.svg", "이수환", ["components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md"], [XMODEL], "XMODEL waveform/stress/integration scope", "model-based verification", "not transistor/post-layout/PCB/silicon"),
        ("FIG-08", "figures/final/FIG-08_signed_stream_handoff.svg", "이수환", ["components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv"], [XMODEL], "Signed-stream SHA256와 canonical output identity", "36 final-test chunks", "identity is not label accuracy"),
        ("FIG-09", "figures/final/FIG-09_digital_validation_hierarchy.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Digital validation hierarchy", "integer reference through board replay", "physical analog not included"),
        ("FIG-10", "figures/final/FIG-10_classification_summary.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Locked classification results", "final-test and model-selection metrics", "public-dataset engineering result"),
        ("FIG-11", "figures/final/FIG-11_confounding_claim_boundary.svg", "양건(편집)", ["docs/DATASET_DOMAIN_CONFOUNDING_KR.md"], ["INTEGRATED"], "Database-class confounding and claim boundary", "generalization interpretation", "does not invalidate RTL/IP evidence"),
        ("FIG-12", "figures/final/FIG-12_digital_processing_flow.svg", "양건(편집)", ["figures/source/approved_svg/FIG-12_digital_processing_flow.svg", "components/digital_accelerator/rtl/snn_ecg_30min_final_top.v", "components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v", "components/digital_accelerator/rtl/core/qrs_lif_detector.v", "components/digital_accelerator/rtl/final_membrane_layer.v", "tables/streaming_state_inventory.csv"], [DIGITAL], "Signed ECG가 사건·QRS 검출을 거쳐 rhythm·morphology 경로로 분기되고, 네 morphology 증거가 서로 독립적인 병렬 경로로 class scoring에 합류한 뒤 60초 Snapshot 30개가 Final Membrane으로 누적되는 digital processing flow", "reader-facing digital architecture with four parallel morphology evidence paths and 30-Snapshot accumulation", "conceptual grouping, not literal post-synthesis netlist connectivity; block internals remain in the body"),
        ("FIG-15", "figures/final/FIG-15_afe_adc_signal_flow.svg", "양건(통합 편집)", ["figures/source/approved_svg/FIG-15_afe_adc_signal_flow.svg", "validation/afe_ltspice_xmodel_aligned/schematics/xmodel_aligned/FULL_AFE_ADC_SH_xmodel_aligned.asc", "components/matlab_prevalidation/matlab_afe_validation/docs/afe_adc_parameter_reference.md", "components/afe_xmodel/analog/ecg_afe_xmodel.sv"], [MATLAB, LTSPICE, XMODEL, "INTEGRATED"], "차동 ECG가 HPF·IA·Active Twin-T notch·LPF와 buffer·12-bit ADC를 통과해 signed stream으로 인계되고, XMODEL 비이상성은 실제 고정 검증 범위에 맞춘 점선 경로로 주입되는 AFE·ADC signal flow", "finite GBW across active op-amp stages, VOS stress at the IA input pair, and one ADC code-boundary injection", "reader-facing architecture; use SPICE-02 for the actual LTspice graphical schematic; neither is physical PCB or silicon evidence"),
        ("FIG-RTL", "figures/final/FIG-RTL_top_with_snapshot_expansion.svg", "양건(통합 편집)", ["figures/source/approved_svg/FIG-RTL_top_with_snapshot_expansion.svg", "artifacts/rtl_elaborated_schematic/FIG-RTL-A_top_hierarchy.svg", "artifacts/rtl_elaborated_schematic/FIG-RTL-B_snapshot_core_hierarchy.svg", "artifacts/rtl_elaborated_schematic/hierarchy_report.txt"], [DIGITAL, "INTEGRATED"], "Pure RTL top hierarchy와 Snapshot core 확장", "Vivado RTL Elaborated Schematic 기반 hierarchy reconstruction", "module instances and connectivity retained; not a synthesized gate-level or post-route netlist"),
    ]
    for fid, source_name, output_name, caption in inherited_matlab_figures:
        figures.append((fid, f"figures/final/{output_name}", "서민우", [f"components/matlab_prevalidation/matlab_afe_validation/figures/{source_name}", "components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md"], [MATLAB], caption, "fixed MATLAB nominal reference figure", "not transistor-level, PCB, silicon, post-layout, or MATLAB-LTspice-XMODEL bit-exact evidence"))
    spice_figures = [
        ("SPICE-01", "SPICE-01_analog_afe_architecture.svg", "AFE+ADC architecture and non-ideality injection points", "schematic/behavioral architecture"),
        ("SPICE-02", "SPICE-02_ltspice_xmodel_aligned_schematic.jpg", "XMODEL-aligned LTspice AFE+ADC/S&H graphical schematic", "actual LTspice schematic capture"),
        ("SPICE-03", "SPICE-03_matlab_ltspice_afe_response.png", "MATLAB and LTspice full AFE frequency-response comparison", "MATLAB-to-schematic design-intent comparison"),
        ("SPICE-04", "SPICE-04_matlab_ltspice_notch_response.png", "MATLAB and LTspice active Twin-T notch comparison", "60 Hz dense response comparison"),
        ("SPICE-05", "SPICE-05_xmodel_ltspice_adc_waveform_full.png", "Full ten-second XMODEL-LTspice ADC waveform overlay", "patient100 nominal 10-second comparison"),
        ("SPICE-06", "SPICE-06_xmodel_ltspice_adc_waveform_zoom.png", "Two-to-three-second XMODEL-LTspice ADC waveform zoom", "QRS-region nominal comparison"),
        ("SPICE-07", "SPICE-07_xmodel_ltspice_adc_error.png", "Per-sample LTspice S/H minus XMODEL ADC error", "ten-second code error"),
        ("SPICE-08", "SPICE-08_xmodel_ltspice_adc_error_histogram.png", "XMODEL-LTspice ADC error histogram", "ten-second code-error distribution"),
        ("SPICE-09", "SPICE-09_xmodel_ltspice_adc_agreement.png", "Cumulative ADC-code agreement by error range", "exact through plus-or-minus 10 LSB coverage"),
        ("SPICE-10", "SPICE-10_xmodel_ltspice_adc_metrics.png", "Quantitative XMODEL-LTspice ADC comparison", "full and settled nominal metrics"),
    ]
    for fid, filename, caption, scope in spice_figures:
        figures.append((fid, f"figures/final/{filename}", "이수환(팀 handoff)", ["figures/source/team_handoff_analog/README.md", "validation/afe_ltspice_xmodel_aligned/tables/xmodel_ltspice_handoff_metrics.csv"], [LTSPICE], caption, scope, "team-provided immutable figure; schematic/behavioral model evidence, not physical PCB or silicon measurement"))
    figures.append((
        "FIG-P05",
        "figures/publication/FIG-P05_vivado_implementation/device_view_annotated_publication.svg",
        "양건(통합 편집)",
        [
            "figures/publication/FIG-P05_vivado_implementation/export_vivado_figures.tcl",
            "figures/publication/FIG-P05_vivado_implementation/extract_hierarchy_placement.tcl",
            "figures/publication/FIG-P05_vivado_implementation/build_annotated_device_figure.py",
            "figures/publication/FIG-P05_vivado_implementation/build_vector_publication.py",
            "figures/publication/FIG-P05_vivado_implementation/evidence_paths.md",
            "figures/publication/FIG-P05_vivado_implementation/device_view_full_original.png",
            "figures/publication/FIG-P05_vivado_implementation/hierarchy_tile_occupancy.csv",
            "figures/publication/FIG-P05_vivado_implementation/placed_tile_occupancy.csv",
            "figures/publication/FIG-P05_vivado_implementation/microblaze_block_design_vivado_native.pdf",
            "figures/publication/FIG-P05_vivado_implementation/worst_setup_path_vivado_native.pdf",
            "components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_timing_summary.rpt",
            "components/digital_accelerator/results/board_replay/microblaze_full_replay/reports/system_utilization_hier.rpt",
        ],
        [DIGITAL, "INTEGRATED"],
        "Actual post-route Device View with hierarchy placement overlay, Vivado native MicroBlaze Block Design와 worst setup path",
        "Vivado 2020.2, xc7a100tcsg324-1, actual Device View plus routed hierarchy/timing evidence",
        "Hierarchy colors use placed primitive coordinates and are not pblock boundaries; not ASIC layout",
    ))
    index = ["# Integrated figure index", "", "Generated integrated figures and immutable team-provided analog validation figures are indexed below. Generated source data: `figures/source/figure_data.json`; analog handoff hashes: `figures/source/team_handoff_analog/README.md`.", ""]
    for fid, path, owner, files, commits, caption, scope, limits in figures:
        index += [f"## {fid}", "", f"- File: `{path}`", f"- Owner: {owner}", f"- Source files: {', '.join(f'`{x}`' for x in files)}", f"- Source commits: {', '.join(commits)}", "- Source-data path: `figures/source/figure_data.json`", f"- Caption: {caption}", f"- Evidence scope: {scope}", f"- Limitations: {limits}", ""]
    (ROOT / "figures" / "FIGURE_INDEX.md").write_text("\n".join(index), encoding="utf-8")
    generated_svg_count = len(list(OUT.glob("FIG-*.svg"))) + len(list(OUT.glob("VAL-*.svg")))
    print(f"generated {generated_svg_count + len(inherited_matlab_figures)} figures ({generated_svg_count} SVG + 7 inherited MATLAB PNG); retained 10 SPICE handoff figures; indexed {len(figures)} including FIG-P05")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
