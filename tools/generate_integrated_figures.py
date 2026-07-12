#!/usr/bin/env python3
"""Generate verified, non-benchmark SVG figures and their provenance index."""

from __future__ import annotations

import html
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "final"
SRC = ROOT / "figures" / "source"
DIGITAL = "c6b80de19cdcad5b7e43fe7835588b629d847f75"
XMODEL = "4756a5086023547328ef44fd5fd87da3c250dc39"
MATLAB = "907f7e1f081a9d6a5703a32095d962143315a192"


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
        "benchmark_status": gm["benchmark"]["status"],
    }
    source_path = SRC / "figure_data.json"
    source_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # FIG-01: motivation
    s = canvas("장시간 ECG 분류 문제", "짧은 박동 정보와 장시간 지속성을 함께 반영")
    s += box(70, 170, 270, 220, "표본값과 박동", ["기울기 · 박동 시점", "QRS · 최고점", "국소 사건 신호"])
    s += box(465, 170, 270, 220, "60초 Snapshot", ["리듬 + 파형 형태", "국소 클래스 증거", "30회 판독"])
    s += box(860, 170, 270, 220, "30분 최종 상태", ["부호 막전위", "장시간 지속성", "승자독식 클래스"])
    s += arrow(340, 280, 465, 280) + arrow(735, 280, 860, 280)
    s.append(txt(600, 500, "핵심: 빠르기 자체가 아니라 시간 계층을 streaming state로 구조화", 24, "#0b7285", 700, "middle"))
    footer(s, "설계 동기를 설명하는 그림이며 임상 진단을 뜻하지 않음")
    write_svg("FIG-01_long_window_motivation.svg", s)

    # FIG-02: compact portrait flowchart following the report's validation flow.
    s = paper_canvas(1200, 1150, "Public ECG data pass through MATLAB prevalidation, parallel XMODEL and RTL development, three verification tracks, a single engineering gate, locked final test, and final reporting")
    s += paper_box(430, 35, 340, 70, "공개 ECG 데이터", "#eff6ff", "#2563a8")
    s += paper_box(400, 145, 400, 75, "MATLAB AFE·ADC 사전검증", "#dbeafe", "#2563a8")
    s += paper_path([(600, 105), (600, 145)])

    s.append(paper_dot(600, 270))
    s += paper_path([(600, 220), (600, 270)], arrow=False)
    s += paper_path([(600, 270), (330, 270), (330, 315)])
    s += paper_path([(600, 270), (870, 270), (870, 315)])
    s += paper_box(160, 315, 340, 80, "AFE·ADC XMODEL 검증", "#dbeafe", "#2563a8")
    s += paper_box(700, 315, 340, 80, "Digital SNN RTL IP", "#dbeafe", "#2563a8")

    s.append(paper_dot(870, 440))
    s += paper_path([(870, 395), (870, 440)], arrow=False)
    s.append(paper_dot(220, 455))
    s += paper_path([(330, 395), (330, 455), (220, 455)], arrow=False)
    s += paper_path([(870, 440), (220, 440), (220, 455)], arrow=False)
    s += paper_box(70, 485, 300, 75, "AFE–RTL 통합 검증", "#ede9fe", "#6b46c1")
    s += paper_box(450, 485, 300, 75, "Accelerator Benchmark", "#ede9fe", "#6b46c1")
    s += paper_box(830, 485, 300, 75, "FPGA·IP 구현 검증", "#ede9fe", "#6b46c1")
    s += paper_path([(220, 455), (220, 485)])
    s += paper_path([(870, 440), (600, 440), (600, 485)])
    s += paper_path([(870, 440), (980, 440), (980, 485)])

    s += paper_path([(220, 560), (220, 610), (600, 610)], arrow=False)
    s += paper_path([(600, 560), (600, 610)], arrow=False)
    s += paper_path([(980, 560), (980, 610), (600, 610)], arrow=False)
    s.append(paper_dot(600, 610))
    s += paper_path([(600, 610), (600, 635)])
    s.append('<polygon points="600,635 820,720 600,805 380,720" fill="#dcfce7" stroke="#2f855a" stroke-width="2.5"/>')
    s.append(txt(600, 713, "설계·통합", 19, "#182230", 700, "middle"))
    s.append(txt(600, 741, "검증 기준 충족?", 19, "#182230", 700, "middle"))

    s += paper_box(900, 680, 250, 80, "모델·RTL 수정", "#fee2e2", "#c53030")
    s += paper_path([(820, 720), (900, 720)])
    s.append(txt(852, 704, "아니오", 15, "#475467", 700, "middle"))
    s += paper_path([(1150, 720), (1170, 720), (1170, 250), (600, 250), (600, 270)])

    s += paper_box(430, 855, 340, 70, "Locked Final Test", "#fef3c7", "#b7791f")
    s += paper_path([(600, 805), (600, 855)])
    s.append(txt(630, 835, "예", 15, "#475467", 700))
    s += paper_box(430, 985, 340, 70, "최종 결과·보고서", "#dbeafe", "#2563a8")
    s += paper_path([(600, 925), (600, 985)])
    s.append('</svg>')
    write_svg("FIG-02_overall_workflow.svg", s)

    # FIG-03 ownership
    s = canvas("Contributor ownership and handoff", "구현 owner·verification owner·integration owner를 분리")
    s += box(70, 150, 300, 310, "서민우 · MATLAB", ["nominal AFE/ADC", "headroom/clipping", "signed vectors", "manifest/hash"], fill="#fff4e6")
    s += box(450, 150, 300, 310, "이수환 · XMODEL", ["non-ideal/stress", "full-record AFE", "SHA256 handoff", "AFE→RTL compare"], fill="#e6fcf5")
    s += box(830, 150, 300, 310, "양건 · Digital/Lead", ["architecture/evaluation", "RTL/Vivado/IP-XACT", "Vitis/board", "final integration"], fill="#e7f5ff")
    s += arrow(370, 305, 450, 305) + arrow(750, 305, 830, 305)
    footer(s, "Collaborative chain does not transfer one contributor's implementation ownership to another")
    write_svg("FIG-03_ownership_handoff.svg", s)

    # FIG-04 architecture
    s = canvas("다중 시간축 구조", "표본값·박동·60초·30분으로 이어지는 상태 계층")
    s += box(50, 180, 220, 220, "12-bit 입력 스트림", ["1 kSPS", "표본값 단위 처리"])
    s += box(335, 150, 250, 280, "사건과 지속 상태", ["박동 시점", "RR 변동", "파형 형태", "최고점 · 조기/지연"])
    s += box(650, 180, 210, 220, "60초 Snapshot", ["60,000표본", "국소 판독"])
    s += box(925, 150, 225, 280, "30분 Final Membrane", ["Snapshot 30개", "부호 누적", "4-Class 승자독식"])
    s += arrow(270, 290, 335, 290) + arrow(585, 290, 650, 290) + arrow(860, 290, 925, 290)
    footer(s, "1,800,000표본 전체를 저장하지 않고 고정 크기 지속 상태만 유지")
    write_svg("FIG-04_multitimescale_architecture.svg", s)

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
    s = canvas("MATLAB nominal pre-validation summary", "대표 NSR/CHF/ARR/AFF 60초 record")
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

    # FIG-12: event path splits into rhythm and morphology evidence, then merges.
    s = paper_canvas(1600, 780, "Signed ECG samples create events and QRS spikes, split into rhythm and morphology evidence paths, and merge into Snapshot and Final Membrane classification")
    s += paper_box(30, 330, 140, 100, "Signed ECG", "#eff6ff", "#2563a8")
    s += paper_box(200, 330, 140, 100, "변화량 계산", "#ecfdf3", "#2f855a")
    s += paper_box(370, 330, 160, 100, "Strong Event", "#ecfdf3", "#2f855a")
    s += paper_box(570, 330, 150, 100, "QRS LIF", "#fffbeb", "#b7791f")
    s += paper_path([(170, 380), (200, 380)])
    s += paper_path([(340, 380), (370, 380)])
    s += paper_path([(530, 380), (570, 380)])

    s.append(txt(900, 80, "박동·리듬 경로", 17, "#475467", 700, "middle"))
    s += paper_box(760, 120, 140, 90, "RR Counter", "#ecfeff", "#0e7490")
    s += paper_box(930, 120, 190, 90, ("PNN·RDM", "Ectopic Evidence"), "#ecfeff", "#0e7490")
    s += paper_path([(720, 380), (740, 380), (740, 165), (760, 165)])
    s += paper_path([(900, 165), (930, 165)])

    s.append(txt(960, 480, "파형 형태 경로", 17, "#475467", 700, "middle"))
    s += paper_path([(450, 430), (450, 500), (1130, 500)], arrow=False)
    s += paper_path([(645, 430), (645, 500)], arrow=False)
    s.append(paper_dot(450, 500, "#667085", 4))
    s.append(paper_dot(645, 500, "#667085", 4))
    morphology = [
        (740, 90, "DSCR"),
        (850, 90, "RAM"),
        (960, 100, "QRS MAF"),
        (1080, 100, "RBBB-like"),
    ]
    for x, w, title in morphology:
        center = x + w / 2
        s.append(paper_dot(center, 500, "#667085", 4))
        s += paper_path([(center, 500), (center, 550)])
        s += paper_box(x, 550, w, 70, title, "#fff7ed", "#c05621")
        s += paper_path([(center, 620), (center, 660)], arrow=False)
    s += paper_path([(785, 660), (1130, 660)], arrow=False)
    s.append(paper_dot(1130, 660))

    s += paper_box(1180, 310, 150, 140, ("60초", "Snapshot"), "#f5f3ff", "#6b46c1")
    s += paper_path([(1120, 165), (1150, 165), (1150, 350), (1180, 350)])
    s += paper_path([(1130, 660), (1150, 660), (1150, 410), (1180, 410)])
    s += paper_box(1370, 300, 150, 160, ("Final", "Membrane"), "#fdf4ff", "#9c36b5")
    s += paper_path([(1330, 380), (1370, 380)])

    s += paper_path([(1520, 330), (1540, 330)], arrow=False)
    s += paper_path([(1520, 370), (1540, 370)], arrow=False)
    s += paper_path([(1520, 410), (1540, 410)], arrow=False)
    s += paper_path([(1520, 450), (1540, 450)], arrow=False)
    s.append(txt(1550, 336, "NSR", 16, "#182230", 700))
    s.append(txt(1550, 376, "CHF", 16, "#182230", 700))
    s.append(txt(1550, 416, "ARR", 16, "#182230", 700))
    s.append(txt(1550, 456, "AFF", 16, "#182230", 700))
    s.append('</svg>')
    write_svg("FIG-12_digital_signal_flow.svg", s)

    # FIG-13: beat/rhythm path with old-state, next-state, and commit boundaries.
    s = canvas("박동·리듬 경로", "ECG 숫자 나열에서 QRS 박동과 RR 간격까지")
    s += box(35, 125, 170, 115, "ECG 숫자 입력", ["… -18, -12, 5, 41 …", "1 ms마다 한 값"], fill="#e7f5ff")
    s += box(245, 125, 180, 115, "현재값-직전값", ["부호 있는 변화량", "상승 / 하강"], fill="#e6fcf5")
    s += box(465, 115, 190, 135, "강한 사건", ["변화 크기>문턱값", "한 클록 펄스"], fill="#e6fcf5")
    s += box(695, 115, 175, 135, "QRS 누적·발화", ["사건 가산", "문턱 발화·초기화", "불응기"], fill="#fff9db")
    s += box(910, 115, 255, 135, "RR·리듬 증거", ["박동 이후 표본 계수", "PNN / RDM", "early↔late 쌍"], fill="#e5dbff")
    s += arrow(205,182,245,182) + arrow(425,182,465,182) + arrow(655,182,695,182) + arrow(870,182,910,182)
    s += box(70, 330, 300, 170, "상태 전이", ["이전 상태 읽기", "다음 상태 계산", "클록에서 확정"], fill="#fff4e6")
    s += box(450, 330, 300, 170, "60초 누적", ["박동/일치/불일치", "RDM 코드", "쌍 횟수"], fill="#fff3bf")
    s += box(830, 330, 300, 170, "다음 단계", ["Snapshot 클래스 상태", "Final 리듬 집계"], fill="#d3f9d8")
    s += arrow(370,415,450,415) + arrow(750,415,830,415)
    footer(s, "설명용 상태 흐름이며 임상 박동·RR annotation을 뜻하지 않음")
    write_svg("FIG-13_beat_rhythm_path.svg", s)

    # FIG-14: morphology path with finite windows and compressed outputs.
    s = canvas("파형 형태 경로", "박동 주변 파형을 유한 레지스터·계수기·코드로 압축")
    s += box(40, 120, 250, 145, "기울기 방향", ["필터 기준", "이전 유효 부호 유지", "방향 전환 펄스"], fill="#e6fcf5")
    s += box(325, 120, 250, 145, "최대 진폭", ["예측 박동 관찰 구간", "문턱 bank 코드", "최댓값+후속 유지"], fill="#e7f5ff")
    s += box(610, 110, 270, 165, "QRS MAF", ["박동 전 120 + 후 100", "폭 · 전환 · 에너지", "pre-QRS 활동"], fill="#fff4e6")
    s += box(915, 110, 250, 165, "말단 지연", ["활동 시작/나이", "말단 관찰 구간", "반복 폭+지연"], fill="#e5dbff")
    s += box(110, 360, 270, 145, "작은 출력 상태", ["전환 펄스", "최대 진폭 코드", "이상 표시"], fill="#fff9db")
    s += box(465, 360, 270, 145, "60초 파형 증거", ["코드 합/횟수", "폭/에너지 사건", "반복 지연 횟수"], fill="#fff3bf")
    s += box(820, 360, 270, 145, "클래스 상태 입력", ["부호 기여값", "Snapshot 파형 형태", "Final 집계"], fill="#d3f9d8")
    s += arrow(380,432,465,432) + arrow(735,432,820,432)
    footer(s, "전체 박동 파형을 저장하지 않고 유한 관찰 상태만 유지")
    write_svg("FIG-14_morphology_path.svg", s)

    # FIG-15: differential input branches merge at the IA; model stresses are
    # shown as separate injection paths rather than as inline signal stages.
    s = paper_canvas(1700, 650, "Differential ECG inputs pass through paired HPFs, merge at the instrumentation amplifier, and continue through notch, low-pass, ADC, and signed digital handoff with separate model-stress injection paths")
    s.append(txt(55, 226, "ECG+", 17, "#182230", 700))
    s.append(txt(55, 386, "ECG−", 17, "#182230", 700))
    s.append(paper_dot(125, 220, "#2563a8", 6))
    s.append(paper_dot(125, 380, "#2563a8", 6))
    s += paper_box(190, 170, 170, 100, "HPF (+)", "#ecfdf3", "#2f855a")
    s += paper_box(190, 330, 170, 100, "HPF (−)", "#ecfdf3", "#2f855a")
    s += paper_path([(131, 220), (190, 220)])
    s += paper_path([(131, 380), (190, 380)])

    s.append('<polygon points="450,145 450,455 650,300" fill="#ecfdf3" stroke="#2f855a" stroke-width="2.5"/>')
    s.append(txt(515, 292, "3-op-amp", 18, "#182230", 700, "middle"))
    s.append(txt(515, 318, "IA", 18, "#182230", 700, "middle"))
    s += paper_path([(360, 220), (450, 220)])
    s += paper_path([(360, 380), (450, 380)])

    s += paper_box(700, 240, 200, 120, ("Active Twin-T", "60 Hz Notch"), "#fff7ed", "#c05621")
    s += paper_box(950, 240, 160, 120, "150 Hz LPF", "#fff7ed", "#c05621")
    s += paper_box(1160, 240, 160, 120, "12-bit ADC", "#f5f3ff", "#6b46c1")
    s += paper_box(1360, 240, 190, 120, ("Signed 12-bit", "Stream"), "#f5f3ff", "#6b46c1")
    s += paper_path([(650, 300), (700, 300)])
    s += paper_path([(900, 300), (950, 300)])
    s += paper_path([(1110, 300), (1160, 300)])
    s += paper_path([(1320, 300), (1360, 300)])
    s += paper_path([(1550, 300), (1590, 300)])
    s.append(txt(1600, 307, "Digital RTL", 18, "#182230", 700))

    s += paper_box(60, 20, 290, 70, "Input Disturbance Injection", "#faf5ff", "#805ad5")
    s += paper_path([(205, 90), (205, 120)], arrow=False, dashed=True, color="#805ad5")
    s += paper_path([(205, 120), (125, 120), (125, 210)], dashed=True, color="#805ad5")
    s += paper_path([(205, 120), (105, 120), (105, 380), (119, 380)], dashed=True, color="#805ad5")
    s += paper_box(650, 20, 380, 70, "R/C Tolerance & Op-Amp Error Model", "#faf5ff", "#805ad5")
    s += paper_path([(840, 90), (840, 125), (550, 125), (550, 160)], dashed=True, color="#805ad5")
    s += paper_path([(840, 125), (800, 125), (800, 240)], dashed=True, color="#805ad5")
    s += paper_path([(840, 125), (1030, 125), (1030, 240)], dashed=True, color="#805ad5")
    s += paper_box(1150, 20, 240, 70, "ADC Error Model", "#faf5ff", "#805ad5")
    s += paper_path([(1270, 90), (1270, 240)], dashed=True, color="#805ad5")
    s.append(txt(850, 600, "Solid arrows: signal path / Dashed arrows: injected disturbance or non-ideal model", 16, "#475467", 600, "middle"))
    s.append('</svg>')
    write_svg("FIG-15_analog_signal_flow.svg", s)

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
        ("FIG-02", "figures/final/FIG-02_overall_workflow.svg", "서민우·이수환·양건", ["source_of_truth/upstream_commits.yaml", "components/digital_accelerator/configs/final_submission_locked_model.json", "components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv", "components/digital_accelerator/reports/final/final_metrics.json"], [MATLAB,XMODEL,DIGITAL], "MATLAB 이후 XMODEL·RTL 개발과 세 검증 경로가 단일 판단 gate로 모이고 잠금 최종시험으로 이어지는 전체 workflow", "compact portrait validation flow with one engineering correction loop", "analog layers are model-based; the locked final test remains outside the correction loop"),
        ("FIG-03", "figures/final/FIG-03_ownership_handoff.svg", "양건(편집)", ["source_of_truth/ownership_matrix.csv"], [MATLAB,XMODEL,DIGITAL], "Contributor ownership과 handoff", "ownership", "collaboration does not transfer implementation ownership"),
        ("FIG-04", "figures/final/FIG-04_multitimescale_architecture.svg", "양건", ["components/digital_accelerator/FINAL_REPORT_KR.md"], [DIGITAL], "60초 Snapshot과 30분 Final Membrane 구조", "locked digital architecture", "SNN-inspired, not trained deep SNN"),
        ("FIG-05", "figures/final/FIG-05_strict_recordwise_protocol.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Strict source-record-wise evaluation protocol", "evaluation protocol", "does not solve database-class confounding"),
        ("FIG-06", "figures/final/FIG-06_matlab_nominal_summary.svg", "서민우", ["components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv"], [MATLAB], "MATLAB representative nominal clipping/headroom", "four selected nominal 60-second records", "not physical measurement"),
        ("FIG-07", "figures/final/FIG-07_xmodel_scope.svg", "이수환", ["components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md"], [XMODEL], "XMODEL waveform/stress/integration scope", "model-based verification", "not transistor/post-layout/PCB/silicon"),
        ("FIG-08", "figures/final/FIG-08_signed_stream_handoff.svg", "이수환", ["components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv"], [XMODEL], "Signed-stream SHA256와 canonical output identity", "36 final-test chunks", "identity is not label accuracy"),
        ("FIG-09", "figures/final/FIG-09_digital_validation_hierarchy.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Digital validation hierarchy", "integer reference through board replay", "physical analog not included"),
        ("FIG-10", "figures/final/FIG-10_classification_summary.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Locked classification results", "final-test and model-selection metrics", "public-dataset engineering result"),
        ("FIG-11", "figures/final/FIG-11_confounding_claim_boundary.svg", "양건(편집)", ["docs/DATASET_DOMAIN_CONFOUNDING_KR.md"], ["INTEGRATED"], "Database-class confounding and claim boundary", "generalization interpretation", "does not invalidate RTL/IP evidence"),
        ("FIG-12", "figures/final/FIG-12_digital_signal_flow.svg", "양건(편집)", ["components/digital_accelerator/rtl/snn_ecg_30min_final_top.v", "components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v", "components/digital_accelerator/rtl/core/qrs_lif_detector.v", "components/digital_accelerator/rtl/final_membrane_layer.v", "tables/streaming_state_inventory.csv"], [DIGITAL], "signed ECG의 사건 경로가 박동·리듬과 파형 형태 경로로 분기된 뒤 Snapshot에서 합류하는 digital signal flow", "branched rhythm and morphology evidence paths with a shared Snapshot merge", "not literal post-synthesis netlist connectivity; block internals remain in the body"),
        ("FIG-13", "figures/final/FIG-13_beat_rhythm_path.svg", "양건(편집)", ["components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v", "components/digital_accelerator/rtl/core/qrs_lif_detector.v", "components/digital_accelerator/rtl/core/pnn_rhythm_predictor.v", "components/digital_accelerator/rtl/core/rdm_variability_neuron.v", "components/digital_accelerator/rtl/core/ectopic_pair_neuron.v"], [DIGITAL], "박동·리듬 state-transition 경로", "reader-facing grouping of fixed RTL state transitions", "conceptual dataflow; literal timing remains in RTL"),
        ("FIG-14", "figures/final/FIG-14_morphology_path.svg", "양건(편집)", ["components/digital_accelerator/rtl/core/dscr_spike_counter.v", "components/digital_accelerator/rtl/core/ram_peak_accumulator.v", "components/digital_accelerator/rtl/core/qrs_maf_neuron.v", "components/digital_accelerator/rtl/core/rbbb_qrs_delay_bank.v"], [DIGITAL], "파형 형태 finite-state 경로", "reader-facing grouping of fixed RTL morphology mechanisms", "engineering proxies; not clinical morphology measurement"),
        ("FIG-15", "figures/final/FIG-15_analog_signal_flow.svg", "양건(통합 편집)", ["components/matlab_prevalidation/matlab_afe_validation/docs/afe_adc_parameter_reference.md", "components/afe_xmodel/analog/ecg_afe_xmodel.sv", "source_of_truth/unresolved_artifacts.csv"], [MATLAB, XMODEL, "INTEGRATED"], "ECG 차동 입력의 두 HPF 경로가 IA에서 합류하고 비이상성 주입 경로가 분리된 analog AFE·ADC signal flow", "differential-input reconstruction with separate XMODEL stress injection paths", "not the missing original LTspice schematic; component values and stress details remain in the body"),
    ]
    for fid, source_name, output_name, caption in inherited_matlab_figures:
        figures.append((fid, f"figures/final/{output_name}", "서민우", [f"components/matlab_prevalidation/matlab_afe_validation/figures/{source_name}", "components/matlab_prevalidation/matlab_afe_validation/figures/FIGURE_CAPTIONS.md"], [MATLAB], caption, "fixed MATLAB nominal reference figure", "not transistor-level, PCB, silicon, post-layout, or MATLAB-XMODEL bit-exact evidence"))
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
    index = ["# Integrated figure index", "", "All figures are generated from verified non-benchmark evidence. Source data: `figures/source/figure_data.json`.", ""]
    for fid, path, owner, files, commits, caption, scope, limits in figures:
        index += [f"## {fid}", "", f"- File: `{path}`", f"- Owner: {owner}", f"- Source files: {', '.join(f'`{x}`' for x in files)}", f"- Source commits: {', '.join(commits)}", "- Source-data path: `figures/source/figure_data.json`", f"- Caption: {caption}", f"- Evidence scope: {scope}", f"- Limitations: {limits}", ""]
    (ROOT / "figures" / "FIGURE_INDEX.md").write_text("\n".join(index), encoding="utf-8")
    print(f"generated 22 figures (15 SVG + 7 inherited MATLAB PNG); indexed {len(figures)} including FIG-P05")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
