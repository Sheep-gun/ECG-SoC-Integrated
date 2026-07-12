#!/usr/bin/env python3
"""Generate verified, non-benchmark SVG figures and their provenance index."""

from __future__ import annotations

import html
import json
from pathlib import Path


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

    # FIG-02: system flow
    s = canvas("전체 시스템 흐름", "모델 기반 AFE·ADC에서 디지털 IP와 FPGA까지")
    xs = [45, 285, 525, 765, 1005]
    titles = ["공개 ECG", "MATLAB", "XMODEL", "디지털 RTL", "FPGA 재생"]
    desc = [["4개 원천 DB"],["공칭 AFE/ADC","기준 벡터"],["교란·비이상성","부호 스트림"],["Snapshot + Final","IP-XACT"],["36개 사례","기능 등가성"]]
    for i,x in enumerate(xs):
        s += box(x, 210, 160, 190, titles[i], desc[i], fill="#e6fffa" if i in (1,2) else "#e8f1fb")
        if i < 4: s += arrow(x+160, 305, xs[i+1], 305)
    footer(s, "아날로그 계층은 모델 기반이며 FPGA는 디지털 통합 증거")
    write_svg("FIG-02_complete_system_flow.svg", s)

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

    # FIG-12: functional Korean labels are primary; module names are secondary.
    s = canvas("디지털 아키텍처", "표본값 → 사건 신호 → 박동·파형 증거 → 60초·30분 상태")
    s += box(35, 125, 150, 90, "입력 ECG 표본값", ["signed 12-bit", "유효 / 준비"], fill="#e7f5ff")
    s += box(225, 115, 185, 110, "파형 변화 사건", ["인접 표본값 차이", "사건 인코더"], fill="#e6fcf5")
    s += box(450, 115, 180, 110, "박동 검출", ["막전위·문턱값", "QRS LIF"], fill="#e6fcf5")
    s += box(670, 115, 205, 110, "박동 간격 측정", ["RR 틱 계수", "PNN 일치/불일치"], fill="#e6fcf5")
    s += box(915, 115, 250, 110, "리듬 분석", ["RR 변화 수준", "RDM · early/late"], fill="#e6fcf5")
    s += arrow(185,170,225,170) + arrow(410,170,450,170) + arrow(630,170,670,170) + arrow(875,170,915,170)
    morphology = [
        (55,"기울기 방향 전환","DSCR · 이전 부호 유지"), (245,"박동 진폭 압축","RAM · 최대 코드"),
        (435,"Early–late 조합","적응형 RR 기준"), (625,"파형 형태 분석","QRS MAF · 유한 이력"),
        (850,"말단 지연 증거","RBBB-like delay"),
    ]
    for x,title,line in morphology:
        s += box(x,280,165 if x != 850 else 210,92,title,[line],fill="#fff4e6")
    s.append('<line x1="110" y1="250" x2="1060" y2="250" stroke="#9fb3c8" stroke-width="3" stroke-dasharray="9 7"/>')
    s.append(txt(600,246,"병렬 유한 사건·상태 경로",14,"#486581",600,"middle"))
    s += box(75,420,240,105,"60초 증거 누적",["사건·코드 계수", "Snapshot 클래스 상태"],fill="#fff9db")
    s += box(370,420,190,105,"60초 상태 확정",["60,000표본", "국소 승자"],fill="#fff3bf")
    s += box(615,420,245,105,"30분 클래스 상태",["부호 Final Membrane", "Snapshot 30개"],fill="#e5dbff")
    s += box(915,410,250,125,"최종 클래스 선택",["guard/rescue/veto", "silent-AFF · WTA", "예측 + 막전위 4개"],fill="#f3d9fa")
    s += arrow(315,472,370,472) + arrow(560,472,615,472) + arrow(860,472,915,472)
    s.append('<rect x="25" y="102" width="1150" height="450" rx="18" fill="none" stroke="#334e68" stroke-width="2" stroke-dasharray="12 8"/>')
    s.append(txt(42,576,"제어 FSM: 수락 표본 · 60,000표본 Snapshot 확정 · 30번째 최종 확정",15,"#102a43",700))
    footer(s, "전체 1,800,000표본 대신 고정 크기 지속 상태를 갱신")
    write_svg("FIG-12_detailed_digital_architecture.svg", s)

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

    figures = [
        ("FIG-01", "figures/final/FIG-01_long_window_motivation.svg", "양건", ["docs/PROBLEM_DEFINITION_KR.md"], ["INTEGRATED"], "장시간 ECG에서 국소 evidence와 장기 persistence를 결합하는 문제 동기", "architectural motivation", "Holter-oriented; not clinical certification"),
        ("FIG-02", "figures/final/FIG-02_complete_system_flow.svg", "서민우·이수환·양건", ["source_of_truth/upstream_commits.yaml"], [MATLAB,XMODEL,DIGITAL], "MATLAB–XMODEL–digital–FPGA 전체 흐름", "component roles and handoffs", "analog layers are model-based"),
        ("FIG-03", "figures/final/FIG-03_ownership_handoff.svg", "양건(편집)", ["source_of_truth/ownership_matrix.csv"], [MATLAB,XMODEL,DIGITAL], "Contributor ownership과 handoff", "ownership", "collaboration does not transfer implementation ownership"),
        ("FIG-04", "figures/final/FIG-04_multitimescale_architecture.svg", "양건", ["components/digital_accelerator/FINAL_REPORT_KR.md"], [DIGITAL], "60초 Snapshot과 30분 Final Membrane 구조", "locked digital architecture", "SNN-inspired, not trained deep SNN"),
        ("FIG-05", "figures/final/FIG-05_strict_recordwise_protocol.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Strict source-record-wise evaluation protocol", "evaluation protocol", "does not solve database-class confounding"),
        ("FIG-06", "figures/final/FIG-06_matlab_nominal_summary.svg", "서민우", ["components/matlab_prevalidation/matlab_afe_validation/results_dataset/afe_dynamic_range_headroom_summary.csv"], [MATLAB], "MATLAB representative nominal clipping/headroom", "four selected nominal 60-second records", "not physical measurement"),
        ("FIG-07", "figures/final/FIG-07_xmodel_scope.svg", "이수환", ["components/afe_xmodel/docs/afe_stress/AFE_xmodel_verification.md"], [XMODEL], "XMODEL waveform/stress/integration scope", "model-based verification", "not transistor/post-layout/PCB/silicon"),
        ("FIG-08", "figures/final/FIG-08_signed_stream_handoff.svg", "이수환", ["components/afe_xmodel/docs/integration_latest/afe_locked_rtl_integration_36case_compare.csv"], [XMODEL], "Signed-stream SHA256와 canonical output identity", "36 final-test chunks", "identity is not label accuracy"),
        ("FIG-09", "figures/final/FIG-09_digital_validation_hierarchy.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Digital validation hierarchy", "integer reference through board replay", "physical analog not included"),
        ("FIG-10", "figures/final/FIG-10_classification_summary.svg", "양건", ["components/digital_accelerator/reports/final/final_metrics.json"], [DIGITAL], "Locked classification results", "final-test and model-selection metrics", "public-dataset engineering result"),
        ("FIG-11", "figures/final/FIG-11_confounding_claim_boundary.svg", "양건(편집)", ["docs/DATASET_DOMAIN_CONFOUNDING_KR.md"], ["INTEGRATED"], "Database-class confounding and claim boundary", "generalization interpretation", "does not invalidate RTL/IP evidence"),
        ("FIG-12", "figures/final/FIG-12_detailed_digital_architecture.svg", "양건(편집)", ["components/digital_accelerator/rtl/snn_ecg_30min_final_top.v", "components/digital_accelerator/rtl/final_membrane_layer.v", "tables/streaming_state_inventory.csv"], [DIGITAL], "독자 개념 중심 디지털 아키텍처", "functional Korean grouping of verified RTL blocks and boundaries", "not literal netlist connectivity; no threshold or benchmark value"),
        ("FIG-13", "figures/final/FIG-13_beat_rhythm_path.svg", "양건(편집)", ["components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v", "components/digital_accelerator/rtl/core/qrs_lif_detector.v", "components/digital_accelerator/rtl/core/pnn_rhythm_predictor.v", "components/digital_accelerator/rtl/core/rdm_variability_neuron.v", "components/digital_accelerator/rtl/core/ectopic_pair_neuron.v"], [DIGITAL], "박동·리듬 state-transition 경로", "reader-facing grouping of fixed RTL state transitions", "conceptual dataflow; literal timing remains in RTL"),
        ("FIG-14", "figures/final/FIG-14_morphology_path.svg", "양건(편집)", ["components/digital_accelerator/rtl/core/dscr_spike_counter.v", "components/digital_accelerator/rtl/core/ram_peak_accumulator.v", "components/digital_accelerator/rtl/core/qrs_maf_neuron.v", "components/digital_accelerator/rtl/core/rbbb_qrs_delay_bank.v"], [DIGITAL], "파형 형태 finite-state 경로", "reader-facing grouping of fixed RTL morphology mechanisms", "engineering proxies; not clinical morphology measurement"),
    ]
    index = ["# Integrated figure index", "", "All figures are generated from verified non-benchmark evidence. Source data: `figures/source/figure_data.json`.", ""]
    for fid, path, owner, files, commits, caption, scope, limits in figures:
        index += [f"## {fid}", "", f"- File: `{path}`", f"- Owner: {owner}", f"- Source files: {', '.join(f'`{x}`' for x in files)}", f"- Source commits: {', '.join(commits)}", "- Source-data path: `figures/source/figure_data.json`", f"- Caption: {caption}", f"- Evidence scope: {scope}", f"- Limitations: {limits}", ""]
    (ROOT / "figures" / "FIGURE_INDEX.md").write_text("\n".join(index), encoding="utf-8")
    print(f"generated {len(figures)} SVG figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
