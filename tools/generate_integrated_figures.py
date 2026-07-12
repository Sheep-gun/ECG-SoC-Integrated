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


def signal_canvas(title: str, subtitle: str) -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">',
        '<defs><marker id="flow-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#34495e"/></marker></defs>',
        '<rect width="1600" height="900" fill="#ffffff"/>',
        '<rect x="0" y="0" width="1600" height="100" fill="#102a43"/>',
        f'<text x="54" y="56" font-family="Arial, Noto Sans KR, sans-serif" font-size="34" font-weight="700" fill="white">{esc(title)}</text>',
        f'<text x="54" y="83" font-family="Arial, Noto Sans KR, sans-serif" font-size="15" fill="#d9e2ec">{esc(subtitle)}</text>',
    ]


def signal_box(x, y, w, h, title, lines=(), accent="#2f80ed", fill="#ffffff") -> list[str]:
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#829ab1" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="8" rx="4" fill="{accent}"/>',
        txt(x + w / 2, y + 42, title, 18, "#102a43", 700, "middle"),
    ]
    start_y = y + 76
    for i, line in enumerate(lines):
        out.append(txt(x + w / 2, start_y + i * 25, line, 15, "#334e68", 400, "middle"))
    return out


def signal_arrow(x1, y1, x2, y2, label="", dashed=False) -> list[str]:
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    out = [f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#34495e" stroke-width="3" marker-end="url(#flow-arrow)"{dash}/>' ]
    if label:
        out.append(txt((x1 + x2) / 2, min(y1, y2) - 10, label, 13, "#486581", 600, "middle"))
    return out


def signal_path(points, label="", dashed=False, color="#34495e") -> list[str]:
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    point_text = " ".join(f"{x},{y}" for x, y in points)
    out = [f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="3" marker-end="url(#flow-arrow)"{dash}/>' ]
    if label:
        x, y = points[len(points) // 2]
        out.append(txt(x, y - 10, label, 13, "#486581", 600, "middle"))
    return out


def signal_footer(lines: list[str], note: str) -> None:
    lines.append('<line x1="40" y1="838" x2="1560" y2="838" stroke="#d9e2ec" stroke-width="2"/>')
    lines.append(txt(800, 870, note, 14, "#486581", 400, "middle"))
    lines.append('</svg>')


def workflow_canvas(title: str, subtitle: str) -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1150" viewBox="0 0 1600 1150">',
        '<defs><marker id="flow-arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#34495e"/></marker></defs>',
        '<rect width="1600" height="1150" fill="#ffffff"/>',
        '<rect x="0" y="0" width="1600" height="100" fill="#102a43"/>',
        f'<text x="54" y="56" font-family="Arial, Noto Sans KR, sans-serif" font-size="34" font-weight="700" fill="white">{esc(title)}</text>',
        f'<text x="54" y="83" font-family="Arial, Noto Sans KR, sans-serif" font-size="15" fill="#d9e2ec">{esc(subtitle)}</text>',
    ]


def workflow_decision(x, y, w, h, lines) -> list[str]:
    points = f"{x + w/2},{y} {x + w},{y + h/2} {x + w/2},{y + h} {x},{y + h/2}"
    out = [f'<polygon points="{points}" fill="#e6fcf5" stroke="#2f9e44" stroke-width="2.5"/>']
    first_y = y + h / 2 - (len(lines) - 1) * 11 + 6
    for i, line in enumerate(lines):
        out.append(txt(x + w / 2, first_y + i * 22, line, 15, "#1b4332", 700, "middle"))
    return out


def workflow_box(x, y, w, h, title, lines=(), accent="#2f80ed", fill="#ffffff") -> list[str]:
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#829ab1" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="8" rx="4" fill="{accent}"/>',
        txt(x + w / 2, y + 34, title, 18, "#102a43", 700, "middle"),
    ]
    for i, line in enumerate(lines):
        out.append(txt(x + w / 2, y + 62 + i * 21, line, 14, "#334e68", 400, "middle"))
    return out


def workflow_footer(lines: list[str], note: str) -> None:
    lines.append('<line x1="40" y1="1090" x2="1560" y2="1090" stroke="#d9e2ec" stroke-width="2"/>')
    lines.append(txt(800, 1125, note, 14, "#486581", 400, "middle"))
    lines.append('</svg>')


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

    # FIG-02: overall research and validation workflow. Iteration arrows stop
    # before the locked final test so the figure cannot imply test-set tuning.
    s = workflow_canvas("전체 연구·검증 workflow", "입력과 provenance 고정 → AFE·ADC 모델 검증 → streaming RTL → FPGA 통합 → 잠금 최종시험")
    s += workflow_box(170, 125, 400, 90, "공개 ECG 데이터", ["NSR·CHF·ARR·AFF 원천 record"], accent="#2f80ed", fill="#f7fbff")
    s += workflow_box(1030, 125, 400, 90, "고정 provenance", ["세 component commit · manifest · SHA256"], accent="#5f3dc4", fill="#faf8ff")
    s += workflow_box(510, 250, 580, 95, "평가 입력과 기준을 먼저 고정", ["record-wise split · 공통 30분 window", "final test는 모델 선택에 사용하지 않음"], accent="#486581", fill="#f5f7fa")
    s += signal_path([(370, 215), (370, 235), (675, 235), (675, 250)])
    s += signal_path([(1230, 215), (1230, 235), (925, 235), (925, 250)])

    rows = [
        (385, "MATLAB 공칭 pre-validation", ["필터·이득·headroom·clipping", "signed 기준 벡터 생성"], ["공칭 기준", "충족?"], "AFE·ADC 파라미터 수정", ["공칭 모델 단계"], "#0ca678", "#f0fff8"),
        (525, "SystemVerilog AFE+ADC XMODEL", ["PLI·R/C mismatch·GBW/VOS", "ADC 비이상성·장시간 stream"], ["stress와 인계", "기준 충족?"], "모델 구현 수정", ["물리 회로 검증 아님"], "#f08c00", "#fff9f0"),
        (665, "정수 reference와 streaming RTL", ["사건·QRS·리듬·형태 → Snapshot", "30개 Snapshot → Final Membrane"], ["reference↔XSim", "일치?"], "RTL 구현 수정", ["locked 구조는 재튜닝하지 않음"], "#7950f2", "#faf7ff"),
        (805, "Vivado implementation · IP · FPGA replay", ["pure RTL → IP-XACT → MicroBlaze", "final_pred·final_mem 비교"], ["통합 등가성", "통과?"], "통합 구현 수정", ["입출력·cadence·연결 교정"], "#1971c2", "#f3f9ff"),
    ]
    for index, (y, title, details, decision, fix_title, fix_lines, accent, fill) in enumerate(rows):
        s.append(f'<circle cx="130" cy="{y + 47.5}" r="22" fill="{accent}"/>')
        s.append(txt(130, y + 54, str(index + 1), 17, "#ffffff", 700, "middle"))
        s += workflow_box(170, y, 500, 95, title, details, accent=accent, fill=fill)
        s += workflow_decision(780, y - 5, 260, 105, decision)
        s += workflow_box(1140, y + 5, 300, 85, fix_title, fix_lines, accent="#e03131", fill="#fff5f5")
        s += signal_arrow(670, y + 47.5, 780, y + 47.5)
        s += signal_arrow(1040, y + 47.5, 1140, y + 47.5, "아니오")
        s += signal_path([(1290, y + 5), (1290, y - 22), (910, y - 22), (910, y - 5)], dashed=True, color="#c92a2a")
        s.append(txt(1100, y - 29, "수정 후 재검증", 13, "#c92a2a", 600, "middle"))
        if index == 0:
            s += signal_path([(800, 345), (800, 365), (420, 365), (420, 385)], "시작")
        else:
            previous_y = rows[index - 1][0]
            s += signal_path([(910, previous_y + 100), (910, y - 18), (420, y - 18), (420, y)], "예")

    s.append(txt(600, 922, "LOCK — 이 아래 결과는 위 설계 단계로 되먹임하지 않음", 15, "#c92a2a", 700, "middle"))
    s.append('<line x1="140" y1="932" x2="1060" y2="932" stroke="#c92a2a" stroke-width="2.5" stroke-dasharray="10 8"/>')
    s += signal_path([(910, 905), (910, 942), (500, 942), (500, 960)])
    s.append(txt(930, 918, "예", 13, "#486581", 600, "start"))
    s += workflow_box(220, 960, 560, 95, "Locked final-test 1회", ["30분 chunk 29/36 · record-majority 16/19", "결과를 모델 선택에 되먹임하지 않음"], accent="#f59f00", fill="#fff9db")
    s += workflow_box(900, 960, 500, 95, "결과·근거·한계 통합", ["성능·자원·benchmark·claim registry", "24시간·physical AFE·clinical validation은 미검증"], accent="#2f80ed", fill="#f3f9ff")
    s += signal_arrow(780, 1007.5, 900, 1007.5)
    workflow_footer(s, "반복 화살표는 공칭·모델·구현 검증에만 적용되며 locked final-test를 이용한 재튜닝 경로는 없다.")
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

    # FIG-12: report-facing digital signal flow. The paths are conceptual
    # groupings of fixed RTL state transitions, not a literal post-synthesis netlist.
    s = signal_canvas("Digital signal flow", "signed ECG 표본 → 강한 변화 사건 → 박동·리듬/파형 증거 → Snapshot → Final Membrane")
    s += signal_box(25, 330, 140, 170, "ECG 표본 입력", ["signed 12-bit", "1 kSPS", "sample_valid"], "#2f80ed", "#f4f8ff")
    s += signal_box(195, 330, 160, 170, "변화량 계산", ["현재값 - 직전값", "상승 / 하강", "표본별 갱신"], "#12b886", "#f1fbf7")
    s += signal_box(385, 330, 170, 170, "강한 변화 사건", ["적응형 문턱값", "rise / fall pulse", "별도 막전위 없음"], "#12b886", "#f1fbf7")
    s += signal_box(585, 330, 170, 170, "QRS LIF", ["사건 가중치 누적", "문턱 발화", "초기화 · 불응기"], "#f59f00", "#fff9e8")
    s += signal_arrow(165, 415, 195, 415, "표본")
    s += signal_arrow(355, 415, 385, 415, "delta")
    s += signal_arrow(555, 415, 585, 415, "event")

    s.append(txt(805, 135, "박동·리듬 경로", 18, "#0b7285", 700))
    s += signal_box(805, 160, 145, 150, "RR 간격", ["박동 이후", "표본 수 계수", "beat tick"], "#0b7285", "#eefafa")
    s += signal_box(980, 150, 195, 170, "리듬 증거", ["PNN 일치/불일치", "RDM 변화 수준", "early↔late 쌍"], "#0b7285", "#eefafa")
    s += signal_path([(755, 415), (780, 415), (780, 235), (805, 235)], "qrs_spike")
    s += signal_arrow(950, 235, 980, 235, "RR")

    s.append(txt(805, 520, "파형 형태 병렬 경로", 18, "#c2410c", 700))
    s.append('<rect x="805" y="540" width="370" height="205" rx="8" fill="#fff8f1" stroke="#f08c46" stroke-width="2"/>')
    for x, y, title, line in [
        (825, 568, "DSCR", "기울기 방향 전환"),
        (995, 568, "RAM", "박동 최대 진폭 코드"),
        (825, 650, "QRS MAF", "폭·복잡도·에너지"),
        (995, 650, "RBBB-like", "말단 반복 지연"),
    ]:
        s.append(f'<rect x="{x}" y="{y}" width="150" height="62" rx="6" fill="#ffffff" stroke="#f08c46"/>')
        s.append(txt(x + 75, y + 24, title, 16, "#102a43", 700, "middle"))
        s.append(txt(x + 75, y + 47, line, 12, "#486581", 400, "middle"))
    s += signal_path([(555, 415), (780, 415), (780, 642), (805, 642)], "표본·event·qrs")

    s += signal_box(1210, 300, 170, 230, "60초 Snapshot", ["60,000표본", "리듬+파형 증거", "NSR/CHF/ARR/AFF", "국소 클래스 상태"], "#7950f2", "#f5f0ff")
    s += signal_path([(1175, 235), (1192, 235), (1192, 365), (1210, 365)], "rhythm")
    s += signal_path([(1175, 642), (1192, 642), (1192, 465), (1210, 465)], "morphology")
    s += signal_box(1410, 300, 165, 230, "Final Membrane", ["Snapshot 30개", "반복·지속성 누적", "guard/rescue/veto", "WTA → 4-class"], "#ae3ec9", "#fbf2ff")
    s += signal_arrow(1380, 415, 1410, 415, "snapshot")
    s.append(txt(1492, 566, "final_pred + final_mem[4]", 15, "#7b2cbf", 700, "middle"))

    s.append('<rect x="120" y="780" width="1360" height="44" rx="6" fill="#edf2f7" stroke="#9fb3c8"/>')
    s.append(txt(800, 808, "제어 FSM: 표본 수락 → 60,000표본 확정 → 30번째 Snapshot 확정 → 최종 출력", 15, "#334e68", 600, "middle"))
    s += signal_path([(260, 780), (260, 520), (95, 520), (95, 500)], dashed=True, color="#829ab1")
    s += signal_path([(1295, 780), (1295, 530)], dashed=True, color="#829ab1")
    s += signal_path([(1492, 780), (1492, 530)], dashed=True, color="#829ab1")
    signal_footer(s, "전체 1,800,000표본을 저장하지 않고 표본별 고정 폭 상태를 갱신하는 설명용 signal flow")
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

    # FIG-15: analog signal flow reconstructed from the fixed MATLAB parameter
    # reference and XMODEL RTL. This is intentionally not the missing LTspice schematic.
    s = signal_canvas("Analog AFE·ADC signal flow", "공개 ECG 차동 전압 → 필터·증폭 → 12-bit 변환 → signed RTL stream")
    s.append(txt(800, 130, "XMODEL에서 가하는 비이상성·교란 입력", 17, "#7c3aed", 700, "middle"))
    s += signal_box(175, 150, 300, 105, "입력 교란", ["baseline wander · 50/60 Hz PLI"], "#8b5cf6", "#faf7ff")
    s += signal_box(650, 150, 300, 105, "아날로그 비이상성", ["R/C mismatch · GBW · VOS"], "#8b5cf6", "#faf7ff")
    s += signal_box(1125, 150, 300, 105, "ADC 비이상성", ["offset · noise · INL/DNL"], "#8b5cf6", "#faf7ff")

    blocks = [
        (25, 330, 120, "ECG 입력", ["차동 전압", "공개 ECG"], "#2f80ed", "#f4f8ff"),
        (170, 330, 140, "HPF", ["10 MΩ · 33 nF", "fc=0.482 Hz", "기준선 이동 억제"], "#12b886", "#f1fbf7"),
        (335, 330, 160, "3-op-amp IA", ["Rfb=100 kΩ", "Rg=1 kΩ", "Av=201"], "#12b886", "#f1fbf7"),
        (520, 330, 200, "Active Twin-T", ["R=26.526 kΩ", "C=100 nF", "k=0.95 · Q≈5", "60 Hz notch+buffer"], "#f59f00", "#fff9e8"),
        (745, 330, 145, "LPF+buffer", ["1 kΩ · 1.06 µF", "fc=150.1 Hz", "ADC 구동"], "#f59f00", "#fff9e8"),
        (915, 330, 155, "12-bit ADC", ["±1.65 V", "1 kSPS", "0.806 mV/LSB"], "#7950f2", "#f5f0ff"),
        (1095, 330, 180, "코드 중심 이동", ["offset 0…4095", "signed=code−2048", "two's-complement"], "#7950f2", "#f5f0ff"),
        (1300, 330, 275, "Digital RTL 인계", ["signed adc_data[11:0]", "sample_valid", "3-digit hex canonical .mem"], "#0b7285", "#eefafa"),
    ]
    for x, y, w, title, desc, accent, fill in blocks:
        s += signal_box(x, y, w, 205, title, desc, accent, fill)
    for x1, x2 in [
        (145, 170), (310, 335), (495, 520), (720, 745),
        (890, 915), (1070, 1095), (1275, 1300),
    ]:
        s += signal_arrow(x1, 432, x2, 432)

    s += signal_path([(325, 255), (325, 292), (240, 292), (240, 330)], dashed=True, color="#8b5cf6")
    s += signal_path([(800, 255), (800, 292), (620, 292), (620, 330)], dashed=True, color="#8b5cf6")
    s += signal_path([(1275, 255), (1275, 292), (992, 292), (992, 330)], dashed=True, color="#8b5cf6")

    s.append('<rect x="120" y="650" width="1360" height="98" rx="8" fill="#f7f9fc" stroke="#bcccdc"/>')
    s.append(txt(150, 682, "MATLAB 공칭 기준", 17, "#102a43", 700))
    s.append(txt(150, 712, "이득·주파수 응답·headroom·ADC code·reference vector", 15, "#486581"))
    s.append(txt(820, 682, "XMODEL 검증", 17, "#102a43", 700))
    s.append(txt(820, 712, "교란·mismatch·op-amp·ADC stress와 장시간 signed stream", 15, "#486581"))
    signal_footer(s, "문서·파라미터·XMODEL RTL 기반 설명용 signal flow이며 원본 LTspice schematic, 물리 PCB 또는 silicon 결과가 아님")
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
        ("FIG-02", "figures/final/FIG-02_overall_workflow.svg", "서민우·이수환·양건", ["source_of_truth/upstream_commits.yaml", "components/digital_accelerator/configs/final_submission_locked_model.json", "components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv", "components/digital_accelerator/reports/final/final_metrics.json"], [MATLAB,XMODEL,DIGITAL], "입력 고정부터 MATLAB–XMODEL–RTL–FPGA–locked final-test까지의 전체 workflow", "component handoffs, engineering correction loops, and one-way locked evaluation", "analog layers are model-based; iteration does not include final-test tuning"),
        ("FIG-03", "figures/final/FIG-03_ownership_handoff.svg", "양건(편집)", ["source_of_truth/ownership_matrix.csv"], [MATLAB,XMODEL,DIGITAL], "Contributor ownership과 handoff", "ownership", "collaboration does not transfer implementation ownership"),
        ("FIG-04", "figures/final/FIG-04_multitimescale_architecture.svg", "양건", ["components/digital_accelerator/FINAL_REPORT_KR.md"], [DIGITAL], "60초 Snapshot과 30분 Final Membrane 구조", "locked digital architecture", "SNN-inspired, not trained deep SNN"),
        ("FIG-05", "figures/final/FIG-05_strict_recordwise_protocol.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Strict source-record-wise evaluation protocol", "evaluation protocol", "does not solve database-class confounding"),
        ("FIG-06", "figures/final/FIG-06_matlab_nominal_summary.svg", "서민우", ["components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv"], [MATLAB], "MATLAB representative nominal clipping/headroom", "four selected nominal 60-second records", "not physical measurement"),
        ("FIG-07", "figures/final/FIG-07_xmodel_scope.svg", "이수환", ["components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md"], [XMODEL], "XMODEL waveform/stress/integration scope", "model-based verification", "not transistor/post-layout/PCB/silicon"),
        ("FIG-08", "figures/final/FIG-08_signed_stream_handoff.svg", "이수환", ["components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv"], [XMODEL], "Signed-stream SHA256와 canonical output identity", "36 final-test chunks", "identity is not label accuracy"),
        ("FIG-09", "figures/final/FIG-09_digital_validation_hierarchy.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Digital validation hierarchy", "integer reference through board replay", "physical analog not included"),
        ("FIG-10", "figures/final/FIG-10_classification_summary.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Locked classification results", "final-test and model-selection metrics", "public-dataset engineering result"),
        ("FIG-11", "figures/final/FIG-11_confounding_claim_boundary.svg", "양건(편집)", ["docs/DATASET_DOMAIN_CONFOUNDING_KR.md"], ["INTEGRATED"], "Database-class confounding and claim boundary", "generalization interpretation", "does not invalidate RTL/IP evidence"),
        ("FIG-12", "figures/final/FIG-12_digital_signal_flow.svg", "양건(편집)", ["components/digital_accelerator/rtl/snn_ecg_30min_final_top.v", "components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v", "components/digital_accelerator/rtl/core/qrs_lif_detector.v", "components/digital_accelerator/rtl/final_membrane_layer.v", "tables/streaming_state_inventory.csv"], [DIGITAL], "signed ECG에서 4-class 출력까지의 digital signal flow", "conceptual grouping of verified RTL state transitions and parallel evidence paths", "not literal post-synthesis netlist connectivity; not clinical feature measurement"),
        ("FIG-13", "figures/final/FIG-13_beat_rhythm_path.svg", "양건(편집)", ["components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v", "components/digital_accelerator/rtl/core/qrs_lif_detector.v", "components/digital_accelerator/rtl/core/pnn_rhythm_predictor.v", "components/digital_accelerator/rtl/core/rdm_variability_neuron.v", "components/digital_accelerator/rtl/core/ectopic_pair_neuron.v"], [DIGITAL], "박동·리듬 state-transition 경로", "reader-facing grouping of fixed RTL state transitions", "conceptual dataflow; literal timing remains in RTL"),
        ("FIG-14", "figures/final/FIG-14_morphology_path.svg", "양건(편집)", ["components/digital_accelerator/rtl/core/dscr_spike_counter.v", "components/digital_accelerator/rtl/core/ram_peak_accumulator.v", "components/digital_accelerator/rtl/core/qrs_maf_neuron.v", "components/digital_accelerator/rtl/core/rbbb_qrs_delay_bank.v"], [DIGITAL], "파형 형태 finite-state 경로", "reader-facing grouping of fixed RTL morphology mechanisms", "engineering proxies; not clinical morphology measurement"),
        ("FIG-15", "figures/final/FIG-15_analog_signal_flow.svg", "양건(통합 편집)", ["components/matlab_prevalidation/matlab_afe_validation/docs/afe_adc_parameter_reference.md", "components/afe_xmodel/analog/ecg_afe_xmodel.sv", "source_of_truth/unresolved_artifacts.csv"], [MATLAB, XMODEL, "INTEGRATED"], "ECG 차동 입력에서 signed RTL stream까지의 analog AFE·ADC signal flow", "reconstruction from fixed parameter documentation and XMODEL RTL", "not the missing original LTspice schematic; not physical or post-layout evidence"),
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
