#!/usr/bin/env python3
"""Fail-closed checks for the reader-centred research-flow technical report."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_KR.md"
CHECKLIST = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_REVIEW_CHECKLIST.md"
EVIDENCE_MAP = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv"
BASELINE_REVIEW = ROOT / "reports" / "BASELINE_PAPER_STRUCTURE_REVIEW_KR.md"
UNRESOLVED_ARTIFACTS = ROOT / "source_of_truth" / "unresolved_artifacts.csv"
RELATED_WORK_AUDIT = ROOT / "docs" / "RELATED_WORK_HOLTER_ECG_KR.md"
BENCHMARK_AUDIT = ROOT / "docs" / "BENCHMARK_IMPORT_AUDIT_KR.md"
TIMING_HISTORY = ROOT / "docs" / "RTL_TIMING_OPTIMIZATION_HISTORY_KR.md"

MAIN_HEADINGS = [
    "# 1. 서론",
    "# 2. 관련 기술과 시스템 설계",
    "# 3. MATLAB 공칭 AFE·ADC 사전검증",
    "# 4. LTspice AFE·ADC 구현과 XMODEL 검증",
    "# 5. 디지털 가속기 IP 설계 및 구현",
    "# 6. 가속기 Benchmark와 아날로그·디지털 통합 검증",
    "# 7. 실험 결과",
    "# 8. 시스템 특성과 적용 범위",
    "# 9. 결론",
]
SUBHEADINGS = [
    "1.1 연구 배경과 문제 정의", "1.2 연구 목표와 주요 기여",
    "2.1 관련 연구가 답하는 질문", "2.2 전체 시스템 흐름과 역할", "2.3 데이터와 평가 원칙",
    "3.1 MATLAB 사전검증의 역할과 흐름", "3.2 공칭 주파수응답과 동적 범위 검증",
    "3.3 기준 벡터 생성과 LTspice 인계",
    "4.1 LTspice AFE·ADC 회로 구현 및 검증", "4.2 LTspice→XMODEL 정합과 비이상성 검증",
    "5.1 핵심 개념과 다중 시간축 처리", "5.2 박동 및 리듬 정보 추출",
    "5.3 파형 형태 및 진폭 정보 추출", "5.4 60초 Snapshot과 30분 Final Membrane",
    "5.5 Streaming state와 하드웨어 구현 방식", "5.6 RTL/IP/FPGA 구현",
    "6.1 가속기 Benchmark 결과와 해석 범위", "6.2 AFE·디지털 통합 XMODEL 검증",
    "7.1 분류 성능", "7.2 Mixed-signal 및 디지털 통합 결과", "7.3 하드웨어 구현 결과",
    "8.1 설계적 차별성과 기술적 의의", "8.2 결과의 적용 범위",
]
REQUIRED_FILES = [
    REPORT, CHECKLIST, EVIDENCE_MAP, BASELINE_REVIEW, UNRESOLVED_ARTIFACTS,
    RELATED_WORK_AUDIT, BENCHMARK_AUDIT, TIMING_HISTORY,
    ROOT / "benchmarks" / "accelerator_benefit" / "results" / "cpu_fpga_comparison.csv",
    ROOT / "benchmarks" / "accelerator_benefit" / "results" / "rtl_cycle_summary.json",
    ROOT / "benchmarks" / "accelerator_benefit" / "results" / "power_energy_summary.csv",
    ROOT / "docs" / "MIXED_SIGNAL_VERIFICATION_KR.md",
    ROOT / "validation" / "afe_ltspice_xmodel_aligned" / "README.md",
    ROOT / "validation" / "afe_ltspice_xmodel_aligned" / "schematics" / "xmodel_aligned" / "FULL_AFE_ADC_SH_xmodel_aligned.asc",
    ROOT / "validation" / "afe_ltspice_xmodel_aligned" / "tables" / "xmodel_aligned_execution_manifest.csv",
    ROOT / "validation" / "afe_ltspice_xmodel_aligned" / "tables" / "xmodel_ltspice_handoff_metrics.csv",
]
REQUIRED_FIGURES = [
    "FIG-01_long_window_motivation.svg", "FIG-02_research_workflow.svg",
    "FIG-08_signed_stream_handoff.svg", "FIG-10_classification_summary.svg",
    "FIG-12_digital_processing_flow.svg",
    "MAT-01_afe_chain_overview.png", "MAT-02_total_frequency_response.png",
    "MAT-03_notch_dense_sweep.png", "MAT-04_dynamic_range_headroom.png",
    "MAT-05_adc_code_distribution.png", "MAT-06_reference_vector_handoff.png",
    "MAT-07_prevalidation_flow.png",
    "SPICE-01_analog_afe_architecture.svg", "SPICE-02_ltspice_xmodel_aligned_schematic.jpg",
    "SPICE-03_matlab_ltspice_afe_response.png", "SPICE-04_matlab_ltspice_notch_response.png",
    "SPICE-05_xmodel_ltspice_adc_waveform_full.png", "SPICE-06_xmodel_ltspice_adc_waveform_zoom.png",
    "SPICE-07_xmodel_ltspice_adc_error.png", "SPICE-08_xmodel_ltspice_adc_error_histogram.png",
    "SPICE-09_xmodel_ltspice_adc_agreement.png", "SPICE-10_xmodel_ltspice_adc_metrics.png",
]
MECHANISM_TERMS = [
    "변화량 = 현재 표본값 - 직전 표본값", "Strong Event 뉴런이 발화했다",
    "별도의 Strong Event 막전위가 있는 것이 아니라", "사건 가중치가 시냅스 가중치 역할",
    "구현된 QRS 검출기의 누설값은 0", "불응기 계수기를 채워",
    "직전 박동 이후 들어온 표본값의 개수", "46개의 기준 눈금",
    "예상과 일치", "현재 RR 간격과 바로 직전 RR 간격의 절대 차이",
    "최근 RR 간격을 천천히 따라가는 기준값", "early→late",
    "현재 표본값 - 필터 기준값", "직전 유효 방향", "최대 진폭 코드",
    "박동 전 120표본", "박동 후 100표본", "첫 강한 사건 위치", "방향 전환 횟수",
    "기준선에서 떨어진 거리", "박동 전 활동 사건", "경과 80~160표본", "90~170표본",
    "여러 번 반복", "승자 횟수", "충돌 억제(guard)", "구조 보강(rescue)",
    "반대 증거 억제(veto)", "조용한 AFF 보정(silent-AFF)", "클 때만",
    "IDLE→CORE_RESET→SEG_START→RUN→SEG_DONE→FLUSH→COMMIT→DONE",
]


def section(text: str, heading: str, level: int) -> str:
    marker = f"{'#' * level} {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    match = re.search(rf"(?m)^#{{1,{level}}} ", text[start:])
    return text[start:start + match.start() if match else len(text)].strip()


def main() -> int:
    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool, detail: object = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(f"{name}: {detail or 'failed'}")

    for path in REQUIRED_FILES:
        check(f"required output {path.name}", path.is_file())
    if not REPORT.is_file():
        return 1

    text = REPORT.read_text(encoding="utf-8-sig")
    numbered = re.findall(r"(?m)^# ([1-9]\d*)\. .+$", text)
    check("exactly nine main chapters", len(numbered) == 9, numbered)
    for heading in MAIN_HEADINGS:
        check(f"main heading {heading}", heading in text)
    for heading in SUBHEADINGS:
        body = section(text, heading, 2)
        check(f"subheading {heading}", bool(body))
        check(f"subsection substantive {heading}", len(body) >= 180, len(body))

    numbered_subs = re.findall(r"(?m)^## \d+\.\d+ .+$", text)
    check("grouped subsection count", len(numbered_subs) == len(SUBHEADINGS), len(numbered_subs))
    module_names = ["ecg_event_encoder", "qrs_lif", "pnn_rhythm", "rdm_", "dscr_", "ram_peak", "qrs_maf", "rbbb_"]
    check("no module-name headings", not any(name in h.lower() for h in numbered_subs for name in module_names))
    chapter3 = section(text, "3. MATLAB 공칭 AFE·ADC 사전검증", 1)
    chapter4 = section(text, "4. LTspice AFE·ADC 구현과 XMODEL 검증", 1)
    chapter5 = section(text, "5. 디지털 가속기 IP 설계 및 구현", 1)
    check("digital architecture remains substantive", len(chapter5) >= 12000, len(chapter5))
    check("MATLAB LTspice and XMODEL depth comparable to digital", len(chapter3) + len(chapter4) >= int(len(chapter5) * 0.65), (len(chapter3), len(chapter4), len(chapter5)))
    check("research-flow chapter order", [text.index(h) for h in MAIN_HEADINGS] == sorted(text.index(h) for h in MAIN_HEADINGS))
    abstract = section(text, "초록", 1)
    abstract_blocks = [block for block in abstract.split("\n\n") if block.strip()]
    check("abstract is concise", 350 <= len(abstract) <= 750, len(abstract))
    check("abstract is one paragraph", len(abstract_blocks) == 1, len(abstract_blocks))
    for term in [
        "본 논문은 장시간 ECG", "SNN-inspired streaming RTL", "평균 절대 오차 0.6445 LSB",
        "29/36=80.56%", "36/36", "BRAM과 DSP 없이", "32.912687배",
    ]:
        check(f"abstract retains essential result {term}", term in abstract)
    chapter2 = section(text, "2. 관련 기술과 시스템 설계", 1)
    check("chapter 2 is concise", 4000 <= len(chapter2) <= 7000, len(chapter2))
    related_work = section(text, "2.1 관련 연구가 답하는 질문", 2)
    related_work_terms = [
        "입력으로 얼마만큼의 ECG를 보고, 마지막에 무엇을 출력하는가",
        "짧게 나타난 질환 증거", "Amirshahi–Hashemi", "N·SVEB·VEB·F",
        "사건 구동형(event-driven)", "지금 이상이 나타났는가",
        "약 48시간 ECG", "향후 심혈관 사망 위험", "9–61초", "DeepHHF",
        "구간 분할과 장시간 통합 흐름은 가장 유사", "본 시스템의 평가 입력은 네 공개 데이터에 공통으로 적용할 수 있는 30분",
        "이상 구간 탐지와 장시간 통합을 입력 기록의 다중 클래스 판정으로 연결",
    ]
    for term in related_work_terms:
        check(f"related-work verified content {term}", term in related_work)
    comparison_header = "| 연구 | 보는 범위 | 마지막에 답하는 질문 | 본 연구와의 차이 |"
    check("related-work comparison table", comparison_header in related_work)
    for row_name in ["Amirshahi–Hashemi", "Bauer et al.", "Chen et al.", "Shanmugam et al.", "Zihlmann et al.", "DeepHHF", "본 연구"]:
        check(f"related-work comparison row {row_name}", f"| {row_name}" in related_work)
    check("no world-first claim", "세계 최초" not in text)
    check("no absolute identical-study claim", "동일한 연구가 없다" not in text)
    check("scoped novelty statement", "검토한 대표 선행연구 범위" in related_work and "문헌 전체에 대한 최초성 주장은 아니다" in related_work)
    system_flow = section(text, "2.2 전체 시스템 흐름과 역할", 2)
    check("chapter 2 question-first system flow", "공개 ECG → MATLAB → LTspice → XMODEL → 디지털 RTL → FPGA" in system_flow)
    check("chapter 2 tool-role table", "| 단계 | 이 단계가 답하는 질문 | 다음 단계로 넘기는 결과 |" in system_flow)
    data_principles = section(text, "2.3 데이터와 평가 원칙", 2)
    for term in ["평가 길이", "네 데이터베이스에 동일하게 적용할 수 있는 실제 기록 길이는 30분", "원천 record 단위 분할은 직접 누출을 막지만"]:
        check(f"chapter 2 data principle {term}", term in data_principles)
    reference_block = text.split("# 참고문헌", 1)[1].split("# 부록 A.", 1)[0]
    reference_numbers = [int(n) for n in re.findall(r"(?m)^\[(\d+)\]", reference_block)]
    check("references sequential 1 through 14", reference_numbers == list(range(1, 15)), reference_numbers)
    for publication_path in [
        "10.1109/TBCAS.2019.2948920", "10.1109/TBCAS.2019.2953001", "ieeexplore.ieee.org/document/9937756",
        "proceedings.mlr.press/v106/shanmugam19a.html", "10.22489/CinC.2017.070-060", "10.1038/s41746-026-02835-8",
    ]:
        check(f"official related-work reference {publication_path}", publication_path in reference_block)
    check("no machine-replacement classification error", "De Novo 클래스ification" not in text)
    related_audit = RELATED_WORK_AUDIT.read_text(encoding="utf-8-sig") if RELATED_WORK_AUDIT.is_file() else ""
    for audit_id in ["RW-001", "RW-002", "RW-003", "RW-004", "RW-005", "RW-006"]:
        check(f"related-work audit {audit_id}", audit_id in related_audit)
    numbered_details = re.findall(r"(?m)^### 5\.[234]\.\d+ .+$", text)
    check("numbered circuit-detail subsections", len(numbered_details) == 14, numbered_details)
    baseline_text = BASELINE_REVIEW.read_text(encoding="utf-8-sig") if BASELINE_REVIEW.is_file() else ""
    for term in ["총 19쪽", "초록", "관련 연구", "회로 설명", "문장과 단락의 공통 형태", "통합 보고서에 적용한 구조"]:
        check(f"baseline-paper audit {term}", term in baseline_text)

    primer = section(text, "5.1 핵심 개념과 다중 시간축 처리", 2)
    for term in ["표본값(sample)", "파형 변화 사건 신호", "막전위형 누적값(membrane state)", "누설(leak)", "문턱값(threshold)", "불응기(refractory", "박동(beat)", "RR 간격", "Snapshot", "Final Membrane"]:
        check(f"concept defined {term}", term in primer)
    check("concepts precede module detail", text.index("**표본값(sample).**") < text.index("ecg_event_encoder_adaptive"))
    check("running signal example", all(token in text for token in ["+  →  +  →  -", "+  →  +  →  +", "회로 흐름을 설명하기 위한 예"]))
    for term in MECHANISM_TERMS:
        check(f"mechanism {term}", term.lower() in text.lower())
    for block in ["ecg_event_encoder_adaptive", "qrs_lif_detector", "pnn_rhythm_predictor", "rdm_variability_neuron", "ectopic_pair_neuron", "dscr_spike_counter", "ram_peak_accumulator", "qrs_maf_neuron", "rbbb_qrs_delay_bank", "class_score_neurons", "final_membrane_layer"]:
        check(f"direct RTL block {block}", block in text)
    timing_optimization = section(text, "Pipeline 구조와 timing closure", 3)
    for term in [
        "C24/global readout", "`*_next` 계수값", "exact lookup table",
        "update–adjust–commit", "timestamp FIFO", "predictor center", "pairwise stage",
        "Pure RTL WNS 8.184 ns", "MicroBlaze 전체 system setup WNS 0.097 ns",
        "36개 시험에서 모두 일치",
    ]:
        check(f"timing optimization content {term}", term in timing_optimization)
    dense_response = section(text, "Dense 신경망의 하드웨어 부담과 제안 구조의 대응", 3)
    for term in [
        "`generic dense neural network`를 FPGA에 이식한 구조가 아니라",
        "domain-specific streaming accelerator", "`multiplier`와 대규모 `MAC` 연산",
        "Pure RTL 구현에서 DSP 0", "Pure RTL 구현에서 BRAM 0",
        "고정 크기 `streaming state`만 표본값 단위로 갱신", "30개 Snapshot의 Final Membrane",
        "2.7 MB의 30분 `raw-input window`를 저장하지 않는다",
    ]:
        check(f"dense response content {term}", term in dense_response)
    timing_history = TIMING_HISTORY.read_text(encoding="utf-8-sig") if TIMING_HISTORY.is_file() else ""
    for term in [
        "c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa", "5e2e5d0a46be47d8086b8642e055066079bfa4e6",
        "c6b80de19cdcad5b7e43fe7835588b629d847f75", "ancestor임을 확인",
        "최종 제출용 저장소 정리 과정에서 삭제", "최적화 전 historical OOC hotspot 수치",
        "critical path 관측 → pipeline 분할 → timing 재검증 → 기능 등가성 확인",
    ]:
        check(f"timing history audit {term}", term in timing_history)
    check("numeric ECG input introduced intuitively", "시간 순서대로 들어오는 부호 있는 숫자의 나열" in text and "회로에는 이 숫자가 P파인지 QRS파인지 알려 주는 표지가 없다" in text)
    internal_jargon = ["token_age", "token age", "토큰 나이", "eval_idx", "age_eval", "qrs_age", "ram_window_open", "prev_slope_sign", "qrs_mem"]
    check("internal signal jargon absent from manuscript", not any(term.lower() in text.lower() for term in internal_jargon), [term for term in internal_jargon if term.lower() in text.lower()])
    check("locked QRS leak configuration", "구현된 QRS 검출기의 누설값은 0" in text and "문턱값 도달 뒤 초기화와 불응기가 중복 박동을 억제한다" in text)
    check("SNN boundary", all(term in text for term in ["학습된 심층 SNN", "STDP", "온라인 학습", "생물물리 뉴런 시뮬레이션", "생물학적 등가성"]))
    cleaned = re.sub(r"```.*?```|`[^`]*`", "", text, flags=re.S)
    # `commit` is intentionally excluded: provenance metadata and Appendix B/C
    # use the Git term, while state updates in the engineering prose are Korean.
    unnecessary_english = ["sample", "event", "state", "window", "baseline", "slope", "sign flip", "amplitude", "morphology", "activity", "readout", "winner", "evidence", "class", "code", "counter", "module", "detector", "output", "input", "pipeline", "reset"]
    english_counts = {term: len(re.findall(rf"(?i)(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", cleaned)) for term in unnecessary_english}
    # The requested reader-facing timing subsection retains one English "pipeline" in its title.
    check("Korean-first prose vocabulary", sum(english_counts.values()) <= 26 and max(english_counts.values()) <= 6, english_counts)
    corruption_markers = ["클래스ifier", "상태s", "표본값s", "계수기s", "관찰 구간를", "진폭가", "사건 신호s"]
    check("no mixed-language replacement corruption", not any(marker in text for marker in corruption_markers), [m for m in corruption_markers if m in text])
    check("consolidated architecture interpretation", "**통합 해석.**" in text)
    body_cleaned = cleaned.split("# 참고문헌", 1)[0]
    expanded_english = ["pattern", "reference", "valid", "strong", "threshold", "current", "previous", "locked", "fixed", "local", "digital", "model", "source", "label", "clinical", "physical", "implementation", "evaluation", "result", "test", "chunk", "segment", "bank", "gate"]
    expanded_counts = {term: len(re.findall(rf"(?i)(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", body_cleaned)) for term in expanded_english}
    check("expanded Korean-first body vocabulary", sum(expanded_counts.values()) <= 35 and max(expanded_counts.values()) <= 4, expanded_counts)

    morphology = section(text, "5.3 파형 형태 및 진폭 정보 추출", 2)
    block_order = [
        ("DSCR purpose before module", "파형이 꺾인 횟수", "`dscr_spike_counter`"),
        ("RAM purpose before module", "30분 전체에서 최고점 하나만 찾으면", "`ram_peak_accumulator`"),
        ("QRS MAF purpose before module", "같은 RR 간격을 가진 박동이라도", "`qrs_maf_neuron`"),
        ("RBBB-like mechanism before module", "활동이 나타난 가장 늦은 위치", "`rbbb_qrs_delay_bank`"),
    ]
    for name, purpose, module in block_order:
        check(name, purpose in morphology and module in morphology and morphology.index(purpose) < morphology.index(module))
    for name, anchor, required in [
        ("DSCR downstream flow", "`dscr_spike_counter`", ["Snapshot의 파형 형태 클래스 누적값"]),
        ("RAM downstream flow", "`ram_peak_accumulator`", ["Snapshot의 진폭 증거", "Final Membrane"]),
        ("QRS MAF downstream flow", "`qrs_maf_neuron`", ["Snapshot의 파형 형태 점수", "Final Membrane"]),
        ("RBBB-like downstream flow", "`rbbb_qrs_delay_bank`", ["Snapshot 클래스 점수", "Final Membrane"]),
    ]:
        check(name, anchor in morphology and all(term in morphology for term in required), required)

    report_images = re.findall(r"!\[[^]]*\]\(([^)]+)\)", text)
    check("twenty-six reader-facing figures", len(report_images) == 26, len(report_images))
    p05_root = ROOT / "figures" / "publication" / "FIG-P05_vivado_implementation"
    for vector_name in ["device_view_annotated_publication.svg", "microblaze_block_design.svg", "worst_setup_path.svg"]:
        check(f"Vivado implementation vector {vector_name}", (p05_root / vector_name).is_file(), str(p05_root / vector_name))
    for annotated_name in ["device_view_full_original.png", "device_view_annotated_publication.pdf", "device_view_annotated_publication.png", "hierarchy_tile_occupancy.csv", "device_grid_bounds.csv"]:
        check(f"annotated Device View evidence {annotated_name}", (p05_root / annotated_name).is_file(), str(p05_root / annotated_name))
    annotated_svg = (p05_root / "device_view_annotated_publication.svg").read_text(encoding="utf-8")
    check("annotated Device View accelerator-only title", "SNN accelerator에 속한 배치 셀만 분리 표시" in annotated_svg)
    check("annotated Device View requested notes removed", "Post-route FPGA Device View. ASIC layout이 아니며" not in annotated_svg and "색상은 routed checkpoint의 실제 placed primitive 좌표이다" not in annotated_svg)
    check("annotated Device View larger panel typography", '.ph{font:700 26px' in annotated_svg and '.lb{font:700 20px' in annotated_svg and '.sm{font:17px' in annotated_svg)
    check("annotated Device View larger region numbering", annotated_svg.count('r="20"') == 5 and '.mk{font:700 22px' in annotated_svg)
    for native_name in ["microblaze_block_design_vivado_native.pdf", "worst_setup_path_vivado_native.pdf"]:
        check(f"Vivado native PDF {native_name}", (p05_root / native_name).is_file(), str(p05_root / native_name))
    legacy_captures = [p05_root / name for name in ["device_view_full.png", "device_view_accelerator_zoom.png", "worst_setup_path.png"]]
    check("no legacy cropped FIG-P05 captures", not any(path.exists() for path in legacy_captures), [str(path) for path in legacy_captures if path.exists()])
    for filename in REQUIRED_FIGURES:
        matches = [p for p in report_images if Path(p).name == filename]
        check(f"figure referenced {filename}", len(matches) == 1, matches)
        check(f"figure exists {filename}", (ROOT / "figures" / "final" / filename).is_file())
    approved_svg_root = ROOT / "figures" / "source" / "approved_svg"
    figure12_path = ROOT / "figures" / "final" / "FIG-12_digital_processing_flow.svg"
    figure15_path = ROOT / "figures" / "final" / "FIG-15_afe_adc_signal_flow.svg"
    figure12_master = approved_svg_root / figure12_path.name
    figure15_master = approved_svg_root / figure15_path.name
    check("FIG-12 approved SVG master exists", figure12_master.is_file(), str(figure12_master))
    check("FIG-15 approved SVG master exists", figure15_master.is_file(), str(figure15_master))
    check("FIG-12 final matches approved SVG master", figure12_master.is_file() and figure12_path.read_bytes() == figure12_master.read_bytes())
    check("FIG-15 final matches approved SVG master", figure15_master.is_file() and figure15_path.read_bytes() == figure15_master.read_bytes())
    figure12 = figure12_path.read_text(encoding="utf-8")
    for label in ["Signed ECG", "ΔECG", "Calculation", "Strong-Event", "Detector", "QRS LIF", "Neuron", "Rhythm Feature Path", "RR Counter", "PNN / RDM /", "Ectopic Evidence", "Morphology Feature Path", "DSCR", "RAM", "QRS MAF", "RBBB-like", "Feature Accumulation", "&amp; Class Scoring", "60s Snapshot", "30-Snapshot", "Accumulation", "30 min Final", "Membrane", "NSR", "CHF", "ARR", "AFF"]:
        check(f"FIG-12 Korean label {label}", label in figure12)
    check("FIG-12 rhythm and morphology branch-merge structure", figure12.count("<polyline") >= 20 and all(label in figure12 for label in ["Rhythm Feature Path", "Morphology Feature Path", "Feature Accumulation"]))
    check("FIG-12 rhythm path preserved", figure12.index("RR Counter") < figure12.index("PNN / RDM /") < figure12.index("Feature Accumulation"))
    morphology_positions = [figure12.index(label) for label in [">DSCR<", ">RAM<", ">QRS MAF<", ">RBBB-like<"]]
    check("FIG-12 four morphology blocks remain independent peers", morphology_positions == sorted(morphology_positions) and len(set(morphology_positions)) == 4)
    check("FIG-12 scoring and 30-Snapshot accumulation explicit", "Feature Accumulation" in figure12 and "30-Snapshot" in figure12 and "30 min Final" in figure12)
    check("FIG-12 white vector canvas", 'fill="#ffffff"' in figure12 and "<svg" in figure12[:400])
    reader_figure_requirements = {
        "FIG-01_long_window_motivation.svg": ["장시간 ECG 분류 문제", "표본값과 박동", "60초 Snapshot", "30분 최종 상태"],
        "FIG-02_research_workflow.svg": ["Public ECG Data", "Record-wise Train / Validation /", "Locked Test Split", "Front End Verification", "(MATLAB, LTspice, XMODEL)", "Digital Model / RTL Development", "Digital Validation", "Criteria Met?", "No", "Yes", "Design Lock", "Locked Test Data", "(Held-out)", "Locked Final Test", "(Used Once Only)", "Implementation Verification", "(RTL / IP / FPGA)", "Analog-Digital Integration Verification", "(XMODEL – RTL End-to-End)", "Final Results &amp; Report"],
        "FIG-08_signed_stream_handoff.svg": ["기능 등가성", "SHA256 동일성", "고정 RTL"],
        "FIG-10_classification_summary.svg": ["분류 결과", "최종 시험 30분 구간", "주 결과"],
        "FIG-15_afe_adc_signal_flow.svg": ["ECG+", "ECG−", "HPF (+)", "HPF (−)", "3-op-amp", "IA", "Active Twin-T", "60 Hz Notch", "150 Hz LPF", "+ Buffer", "12-bit ADC", "Signed 12-bit", "Stream", "Digital", "RTL", "Input Disturbance Injection", "R/C Mismatch Model", "Op-Amp GBW / VOS Model", "ADC Non-Ideality Injection", "Solid arrows: signal path / Dashed arrows: injected disturbance or non-ideal model"],
    }
    for filename, labels in reader_figure_requirements.items():
        svg = (ROOT / "figures" / "final" / filename).read_text(encoding="utf-8")
        for label in labels:
            check(f"reader-facing figure label {filename}: {label}", label in svg)
    figure02 = (ROOT / "figures" / "final" / "FIG-02_research_workflow.svg").read_text(encoding="utf-8")
    figure15 = figure15_path.read_text(encoding="utf-8")
    check("FIG-02 data-separated validation flow with pre-lock correction loop", "<polygon" in figure02 and figure02.count("<polyline") >= 12)
    check("FIG-02 locked test follows Design Lock in the main path", figure02.index("Design Lock") < figure02.index("Locked Final Test") and "(Used Once Only)" in figure02)
    check("FIG-02 correction loop returns only to digital development", 'points="310,730 120,730 120,530 250,530' in figure02 and "Digital Model / RTL Development" in figure02)
    main_workflow_rects = re.findall(r'<rect x="250" y="(?:30|180|330|480|880|1030|1180|1330|1480)" width="600" height="100"', figure02)
    check("FIG-02 main blocks share width and center axis", len(main_workflow_rects) == 9, len(main_workflow_rects))
    check("FIG-02 held-out data feeds only Locked Final Test", figure02.count('points="1045,430 1045,1080 850,1080') == 1)
    check("FIG-02 post-lock central flow has no branch", all(path in figure02 for path in ['points="550,980 550,1030', 'points="550,1130 550,1180', 'points="550,1280 550,1330', 'points="550,1430 550,1480']))
    check("FIG-02 white vector canvas", 'fill="#ffffff"' in figure02 and figure02.lstrip().startswith("<svg"))
    check("FIG-15 differential merge and stress injection", "<polygon" in figure15 and figure15.count("stroke-dasharray") >= 8)
    check("FIG-15 approved stress labels retained", all(label in figure15 for label in ["Input Disturbance Injection", "R/C Mismatch Model", "Op-Amp GBW / VOS Model", "ADC Non-Ideality Injection"]))
    check("FIG-15 ADC output code boundary retained", 'points="1360,393 1385,393"' in figure15 and "marker-mid:url(#Dot)" in figure15)
    check("FIG-15 white vector canvas", 'fill="#ffffff"' in figure15 and "<svg" in figure15[:500])
    check("reader-facing caption states parallel morphology grouping", "네 파형 형태 블록은 독자를 위한 개념적 묶음" in text and "실제 post-synthesis netlist 연결을 뜻하지 않는다" in text)
    check("reader-facing caption states analog stress scope", "유한 GBW는 능동 연산증폭기 단계 전체에서 평가했고 VOS 스트레스는 IA 입력쌍에 적용했다" in text)
    check("reader-facing caption forbids post-lock retuning", "FPGA 단계에서는 설계를 다시 조정하지 않고 같은 결과가 재현되는지만 확인한다" in text)
    old_english_figure_phrases = ["Sample / Beat", "60-second Snapshot", "Event / State", "Signed-stream handoff integrity", "Locked classification result", "old state 읽기", "Peak 진폭", "Class 상태 입력"]
    used_svg_text = "\n".join((ROOT / "figures" / "final" / filename).read_text(encoding="utf-8") for filename in reader_figure_requirements)
    check("old English-heavy figure labels absent", not any(phrase in used_svg_text for phrase in old_english_figure_phrases), [p for p in old_english_figure_phrases if p in used_svg_text])

    afe = section(text, "4.1 LTspice AFE·ADC 회로 구현 및 검증", 2)
    for term in [
        "ECG 입력 → HPF → 3-op-amp IA → active Twin-T 60 Hz notch와 buffer → 150 Hz LPF와 buffer → 12-bit ADC → offset-binary → signed two’s-complement stream",
        "Av_IA = 1 + 2Rfb/Rg", "100 kΩ", "1 kΩ", "0.482287706339 Hz", "10 MΩ", "33 nF",
        "R=26.526 kΩ", "C=100 nF", "Rk1=5 kΩ", "Rk2=95 kΩ", "Q≈1/[4(1−k)]=5",
        "1.06 µF", "150.146172728 Hz", "LSB=3.3/4095=0.000805860805861 V",
        "offset_binary = floor", "signed_decimal = offset_binary − 2048", "$fstrobe",
        "FULL_AFE_ADC_SH_xmodel_aligned.asc", "35개 nominal/stress 실행", "SPICE-02_ltspice_xmodel_aligned_schematic.jpg",
    ]:
        check(f"AFE design detail {term}", term in afe)
    for term in ["vcvs", "110 dB", "active Twin-T", "unity buffer", "1.06 µF", "$fstrobe"]:
        check(f"final AFE construction {term}", term.lower() in afe.lower())

    analog_validation = "\n".join([
        section(text, "3. MATLAB 공칭 AFE·ADC 사전검증", 1),
        section(text, "4.2 LTspice→XMODEL 정합과 비이상성 검증", 2),
        section(text, "6.2 AFE·디지털 통합 XMODEL 검증", 2),
    ])
    for term in [
        "MATLAB은 공칭", "LTspice", "XMODEL", "평균 RMS 차이는 1.95 LSB", "60 Hz 간섭의 잔류는 RMS 0.92 mV",
        "50 Hz에서는 118 mV", "100.7 dB", "80.0 dB", "100 kHz", "2.04 code",
        "train/val/test 1,200개 모두 0", "shift 중앙값 1.0 ms", "RR 오차 중앙값 0 ms",
        "final_pred 15/16", "SHA256 36/36", "final_pred", "final_mem", "평균 절대 오차는 0.6445 LSB",
        "시간 지연은 0표본", "±5 LSB", "98.74%", "±10 LSB", "99.89%",
    ]:
        check(f"MATLAB XMODEL verification {term}", term in analog_validation)
    for source_name in [
        "fig_afe_chain_overview.png", "fig_total_frequency_response.png", "fig_notch_dense_sweep.png",
        "fig_dynamic_range_headroom.png", "fig_adc_code_distribution.png",
        "fig_reference_vector_handoff.png", "fig_matlab_prevalidation_flow.png",
    ]:
        check(f"fixed MATLAB figure cited {source_name}", source_name in text)
    direct_evidence_captions = re.findall(r"(?m)^\*그림 (?:3|4[a-d]?|5|6[a-b]?|7|8|9|10[a-d]?|13|15[a-b]?)\..*\[직접 근거:.*\]\*$", text)
    check("AFE figures have direct evidence captions", len(direct_evidence_captions) == 18, len(direct_evidence_captions))
    unresolved_text = UNRESOLVED_ARTIFACTS.read_text(encoding="utf-8-sig")
    check("LTspice schematic resolution recorded", "RESOLVED_IMPORTED" in unresolved_text and "FULL_AFE_ADC_SH_xmodel_aligned.asc" in unresolved_text)
    check("LTspice schematic present", (ROOT / "validation" / "afe_ltspice_xmodel_aligned" / "schematics" / "xmodel_aligned" / "FULL_AFE_ADC_SH_xmodel_aligned.asc").is_file())
    check("no fixed component ASC schematic", not any((ROOT / p).suffix.lower() == ".asc" for p in [str(x.relative_to(ROOT)) for root in [ROOT / "components" / "matlab_prevalidation", ROOT / "components" / "afe_xmodel"] for x in root.rglob("*") if x.is_file()]), "unexpected .asc present")

    for value in ["29/36=80.56%", "16/19=84.21%", "9,719 LUT", "5,038 FF", "BRAM 0", "DSP 0", "8.184 ns", "1.95 LSB", "1.019633440086 V", "0.92 mV", "100.7 dB", "15/16", "21,600,000 bits", "2.04 code", "0.00007%", "0.481174 Hz", "200.594 V/V", "−83.557 dB", "150.211 Hz", "10,000", "0.6445 LSB", "0.999518", "98.74%", "99.89%", "1,777.699800 ms", "2,007.549250 ms", "54.012600 ms", "33,325,557.369947 samples/s", "32.912687×", "0.099 W", "0.005347247400 J/decision"]:
        check(f"required result {value}", value in text)
    for name, meaning in [
        ("60 Hz attenuation meaning", "간섭 진폭을 약 1/15,000로 줄인다는 뜻"),
        ("sub-LSB handoff meaning", "평균 오차는 0.6445 LSB로 ADC 한 단계보다 작았고"),
        ("classification count meaning", "36개 구간 중 29개를 맞히고 7개를 틀렸다"),
        ("equivalence meaning", "분류 정확도가 100%라는 뜻이 아니라"),
    ]:
        check(name, meaning in text)
    check("LTspice results include reader meaning column", "| 확인한 성능 | LTspice 결과 | 이 결과가 뜻하는 것 |" in text)
    benchmark_section = section(text, "6.1 가속기 Benchmark 결과와 해석 범위", 2)
    for term in [
        "09e4d840", "최종 예측 36/36", "네 막전위 144/144", "Snapshot 경계 1,080/1,080",
        "hand-written single-thread transaction-level Exact C++", "Python 주기 모델은 검증용", "Verilator host runtime도 RTL simulation",
        "5,401,260 cycles", "100 MHz", "speedup estimate", "측정 보드 speedup", "30분이 걸리므로 live 환경의 최종 판정시간이 54 ms가 되는 것은 아니다",
        "Vivado 추정 전력", "PENDING_BOARD",
    ]:
        check(f"benchmark scope {term}", term in benchmark_section)
    check("old benchmark import placeholder absent", "PENDING_EXTERNAL_BENCHMARK_IMPORT" not in text)
    check("validation boundary", "학습·검증 결과는 모델을 선택하는 데 사용했기 때문에 최종 성능으로 보지 않는다" in text and "| 검증 | 32/32 | 100.00% | — | 모델 선택 전용 |" in text)
    check("equivalence not accuracy", "classifier의 정답 표지 정확도를 100%로 만들지는 않는다" in text)
    check("dataset confounding", "원천 record 단위 분할은 직접 누출을 막지만" in text.lower())
    for term in [
        "본 시스템의 평가 단위는 30분 ECG",
        "48개의 30분 excerpt",
        "클래스마다 실제 관찰 길이를 동일하게 유지",
        "특정 클래스만 반복하거나 빈 값을 채우지 않고",
        "60초 Snapshot × 30개",
        "CLM-035",
    ]:
        check(f"30-minute window rationale {term}", term in text)
    dataset_method = (ROOT / "docs" / "DATASET_AND_EVALUATION_KR.md").read_text(encoding="utf-8-sig")
    check("dataset method records 30-minute rationale", all(term in dataset_method for term in ["24/48시간 Holter형", "48개의 half-hour", "1,800,000 samples", "임상적 24시간 Holter를 대체하거나 동등"]), "dataset window rationale incomplete")
    check("analog result scope", "아날로그 결과는 MATLAB 공칭 모델, ±1.65 V LTspice schematic과 SystemVerilog XMODEL" in text)

    metrics = json.loads((ROOT / "source_of_truth" / "global_metrics.yaml").read_text(encoding="utf-8"))
    check("global final metric", metrics["metrics"]["final_test_chunk_accuracy"]["value"] == 80.56)
    benchmark = metrics["benchmark"]
    check("benchmark imported status", benchmark["status"] == "IMPORTED_VERIFIED_NO_BOARD")
    check("benchmark commit exact", benchmark["upstream_commit"] == "09e4d840827ad20856f5e23be4743ddd01565e30")
    check("benchmark Exact C++ latency exact", benchmark["cpu_kernel_latency_ms"] == 1777.6998 and benchmark["cpu_end_to_end_latency_ms"] == 2007.54925)
    check("benchmark RTL exact", benchmark["rtl_processing_latency_ms"] == 54.0126 and benchmark["rtl_throughput_samples_per_s"] == 33325557.369947)
    check("benchmark speedup exact", round(benchmark["exact_cpp_to_rtl_speedup_estimate"], 6) == 32.912687)
    check("benchmark estimated power exact", benchmark["estimated_power_w"] == 0.099 and benchmark["estimated_energy_per_decision_j"] == 0.0053472474)
    check("physical board metrics pending", benchmark["measured_board_power_w"] is None and benchmark["measured_energy_per_decision_j"] is None and benchmark["board_timing_status"] == "PENDING_BOARD")
    with (ROOT / "source_of_truth" / "claim_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        claim_rows = list(csv.DictReader(handle))
    known = {row["claim_id"] for row in claim_rows}
    claim_map = {row["claim_id"]: row for row in claim_rows}
    check("CLM-048 timing history registered", claim_map.get("CLM-048", {}).get("status") == "CAREFUL")
    check("CLM-048 commit chain", all(commit in claim_map.get("CLM-048", {}).get("upstream_commit", "") for commit in ["c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa", "5e2e5d0a46be47d8086b8642e055066079bfa4e6", "c6b80de19cdcad5b7e43fe7835588b629d847f75"]))
    check("CLM-048 historical limitation", "17.5k LUT" in claim_map.get("CLM-048", {}).get("limitations", ""))
    with EVIDENCE_MAP.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {"section", "statement_id", "summarized_statement", "claim_id", "evidence_path", "upstream_repository", "upstream_commit", "owner", "status", "limitation"}
    check("evidence-map schema", bool(rows) and set(rows[0]) == required_columns)
    check("evidence-map coverage", len(rows) >= 66, len(rows))
    valid_sections = {"초록", "부록"} | {str(i) for i in range(1, 10)} | {s.split()[0] for s in SUBHEADINGS}
    for row in rows:
        check(f"map section {row['statement_id']}", row["section"] in valid_sections, row["section"])
        check(f"map path {row['statement_id']}", (ROOT / row["evidence_path"]).exists(), row["evidence_path"])
        used = set(re.findall(r"CLM-\d{3}", row["claim_id"]))
        check(f"map claims {row['statement_id']}", used.issubset(known), used - known)

    inline_paths = re.findall(r"`((?:components|datasets|docs|tables|figures|source_of_truth|benchmarks|reports)/[^`]+)`", text)
    for relative in inline_paths:
        check(f"inline path {relative}", (ROOT / relative).exists())
    registered_owners = {row["owner"] for row in claim_rows}
    check("component owners registered", {"서민우", "이수환", "양건"}.issubset(registered_owners), registered_owners)
    check("no private email", re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I) is None)
    check("no personal path", re.search(r"[A-Z]:[\\/]Users[\\/]", text, re.I) is None)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    check("README report link", "[최종 통합 기술보고서 핵심 원고 보기](reports/INTEGRATED_TECHNICAL_REPORT_KR.md)" in readme)
    print(f"{'PASS' if not failures else 'FAIL'}: {checks} report rules, {len(failures)} conflicts, chars={len(text)}, figures={len(report_images)}, evidence_rows={len(rows)}")
    for failure in failures:
        print(f"- {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
