#!/usr/bin/env python3
"""Fail-closed checks for the reader-centred seven-chapter technical report."""

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

MAIN_HEADINGS = [
    "# 1. 서론",
    "# 2. 관련 기술과 시스템 설계",
    "# 3. 제안 SNN-Inspired 디지털 아키텍처",
    "# 4. 구현 및 검증 방법",
    "# 5. 실험 결과",
    "# 6. 종합 논의와 한계",
    "# 7. 결론",
]
SUBHEADINGS = [
    "1.1 연구 배경과 문제 정의", "1.2 연구 목표와 주요 기여",
    "2.1 기존 접근의 한계와 설계 요구", "2.2 데이터셋과 평가 프로토콜",
    "3.1 핵심 개념과 다중 시간축 처리", "3.2 박동 및 리듬 정보 추출",
    "3.3 파형 형태 및 진폭 정보 추출", "3.4 60초 Snapshot과 30분 Final Membrane",
    "3.5 Streaming state와 하드웨어 구현 방식",
    "4.1 AFE·ADC 모델 검증", "4.2 RTL/IP/FPGA 구현", "4.3 End-to-end 기능 등가성 검증",
    "5.1 분류 성능", "5.2 Mixed-signal 및 디지털 통합 결과", "5.3 하드웨어 구현 결과",
    "6.1 설계적 차별성과 기술적 의의", "6.2 결과의 해석 범위와 향후 과제",
]
REQUIRED_FILES = [REPORT, CHECKLIST, EVIDENCE_MAP, BASELINE_REVIEW]
REQUIRED_FIGURES = [
    "FIG-01_long_window_motivation.svg", "FIG-02_complete_system_flow.svg",
    "FIG-04_multitimescale_architecture.svg", "FIG-08_signed_stream_handoff.svg",
    "FIG-10_classification_summary.svg", "FIG-12_detailed_digital_architecture.svg",
    "FIG-13_beat_rhythm_path.svg", "FIG-14_morphology_path.svg",
]
MECHANISM_TERMS = [
    "변화량 = 현재 표본값 - 직전 표본값", "Strong Event 뉴런이 발화했다",
    "별도의 Strong Event 막전위가 있는 것이 아니라", "사건 가중치가 시냅스 가중치 역할",
    "현재 고정 설정의 QRS 누설량은 0", "불응기 계수기를 채워",
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
    check("exactly seven main chapters", len(numbered) == 7, numbered)
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
    check("chapter 3 is longest", len(section(text, "3. 제안 SNN-Inspired 디지털 아키텍처", 1)) == max(len(section(text, h[2:], 1)) for h in MAIN_HEADINGS), "chapter lengths")
    chapter2 = section(text, "2. 관련 기술과 시스템 설계", 1)
    for term in ["전체 파형을 저장", "짧은 구간의 파형", "학습된 심층 SNN", "설계 요구", "전체 신호 흐름"]:
        check(f"related-work design gap {term}", term in chapter2)
    numbered_details = re.findall(r"(?m)^### 3\.[234]\.\d+ .+$", text)
    check("numbered circuit-detail subsections", len(numbered_details) == 14, numbered_details)
    baseline_text = BASELINE_REVIEW.read_text(encoding="utf-8-sig") if BASELINE_REVIEW.is_file() else ""
    for term in ["총 19쪽", "초록", "관련 연구", "회로 설명", "문장과 단락의 공통 형태", "통합 보고서에 적용한 구조"]:
        check(f"baseline-paper audit {term}", term in baseline_text)

    primer = section(text, "3.1 핵심 개념과 다중 시간축 처리", 2)
    for term in ["표본값(sample)", "사건 신호(event)", "막전위형 누적값(membrane state)", "누설(leak)", "문턱값(threshold)", "불응기(refractory", "박동(beat)", "RR 간격", "Snapshot", "Final Membrane"]:
        check(f"concept defined {term}", term in primer)
    check("concepts precede module detail", text.index("**표본값(sample).**") < text.index("ecg_event_encoder_adaptive"))
    check("running signal example", all(token in text for token in ["+  →  +  →  -", "+  →  +  →  +", "회로 흐름을 설명하기 위한 예"]))
    for term in MECHANISM_TERMS:
        check(f"mechanism {term}", term.lower() in text.lower())
    for block in ["ecg_event_encoder_adaptive", "qrs_lif_detector", "pnn_rhythm_predictor", "rdm_variability_neuron", "ectopic_pair_neuron", "dscr_spike_counter", "ram_peak_accumulator", "qrs_maf_neuron", "rbbb_qrs_delay_bank", "class_score_neurons", "final_membrane_layer"]:
        check(f"direct RTL block {block}", block in text)
    check("numeric ECG input introduced intuitively", "시간 순서대로 들어오는 부호 있는 숫자의 나열" in text and "회로에는 이 숫자가 P파인지 QRS파인지 알려 주는 표지가 없다" in text)
    internal_jargon = ["token_age", "token age", "토큰 나이", "eval_idx", "age_eval", "qrs_age", "ram_window_open", "prev_slope_sign", "qrs_mem"]
    check("internal signal jargon absent from manuscript", not any(term.lower() in text.lower() for term in internal_jargon), [term for term in internal_jargon if term.lower() in text.lower()])
    check("locked QRS leak nuance", "현재 고정 설정의 QRS 누설량은 0" in text and "현재 설정의 누설이 그 시간 간격을 강제하는 것은 아니다" in text)
    check("SNN boundary", all(term in text for term in ["학습된 심층 SNN", "STDP", "온라인 학습", "생물물리 뉴런 시뮬레이션", "생물학적 등가성"]))
    cleaned = re.sub(r"```.*?```|`[^`]*`", "", text, flags=re.S)
    # `commit` is intentionally excluded: provenance metadata and Appendix B/C
    # use the Git term, while state updates in the engineering prose are Korean.
    unnecessary_english = ["sample", "event", "state", "window", "baseline", "slope", "sign flip", "amplitude", "morphology", "activity", "readout", "winner", "evidence", "class", "code", "counter", "module", "detector", "output", "input", "pipeline", "reset"]
    english_counts = {term: len(re.findall(rf"(?i)(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", cleaned)) for term in unnecessary_english}
    check("Korean-first prose vocabulary", sum(english_counts.values()) <= 25 and max(english_counts.values()) <= 6, english_counts)
    corruption_markers = ["클래스ifier", "상태s", "표본값s", "계수기s", "관찰 구간를", "진폭가", "사건 신호s"]
    check("no mixed-language replacement corruption", not any(marker in text for marker in corruption_markers), [m for m in corruption_markers if m in text])
    check("two consolidated architecture boundaries", text.count("**통합 해석 경계.**") == 2, text.count("**통합 해석 경계.**"))
    body_cleaned = cleaned.split("# 참고문헌", 1)[0]
    expanded_english = ["pattern", "reference", "valid", "strong", "threshold", "current", "previous", "locked", "fixed", "local", "digital", "model", "source", "label", "clinical", "physical", "implementation", "evaluation", "result", "test", "chunk", "segment", "bank", "gate"]
    expanded_counts = {term: len(re.findall(rf"(?i)(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", body_cleaned)) for term in expanded_english}
    check("expanded Korean-first body vocabulary", sum(expanded_counts.values()) <= 35 and max(expanded_counts.values()) <= 4, expanded_counts)

    morphology = section(text, "3.3 파형 형태 및 진폭 정보 추출", 2)
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
    check("eight reader-facing figures", len(report_images) == 8, len(report_images))
    for filename in REQUIRED_FIGURES:
        matches = [p for p in report_images if Path(p).name == filename]
        check(f"figure referenced {filename}", len(matches) == 1, matches)
        check(f"figure exists {filename}", (ROOT / "figures" / "final" / filename).is_file())
    figure12 = (ROOT / "figures" / "final" / "FIG-12_detailed_digital_architecture.svg").read_text(encoding="utf-8")
    for label in ["입력 ECG 표본값", "파형 변화 사건", "박동 검출", "박동 간격 측정", "리듬 분석", "60초 증거 누적", "30분 클래스 상태", "최종 클래스 선택"]:
        check(f"FIG-12 Korean label {label}", label in figure12)
    reader_figure_requirements = {
        "FIG-01_long_window_motivation.svg": ["장시간 ECG 분류 문제", "표본값과 박동", "60초 Snapshot", "30분 최종 상태"],
        "FIG-02_complete_system_flow.svg": ["전체 시스템 흐름", "공개 ECG", "디지털 RTL", "FPGA 재생"],
        "FIG-04_multitimescale_architecture.svg": ["다중 시간축 구조", "사건과 지속 상태", "60초 Snapshot", "30분 Final Membrane"],
        "FIG-08_signed_stream_handoff.svg": ["기능 등가성", "SHA256 동일성", "고정 RTL"],
        "FIG-10_classification_summary.svg": ["분류 결과", "최종 시험 30분 구간", "주 결과"],
        "FIG-13_beat_rhythm_path.svg": ["박동·리듬 경로", "ECG 숫자 입력", "현재값-직전값", "강한 사건", "QRS 누적·발화", "박동 이후 표본 계수"],
        "FIG-14_morphology_path.svg": ["파형 형태 경로", "이전 유효 부호 유지", "예측 박동 관찰 구간", "말단 관찰 구간"],
    }
    for filename, labels in reader_figure_requirements.items():
        svg = (ROOT / "figures" / "final" / filename).read_text(encoding="utf-8")
        for label in labels:
            check(f"reader-facing figure label {filename}: {label}", label in svg)
    old_english_figure_phrases = ["Sample / Beat", "60-second Snapshot", "Event / State", "Signed-stream handoff integrity", "Locked classification result", "old state 읽기", "Peak 진폭", "Class 상태 입력"]
    used_svg_text = "\n".join((ROOT / "figures" / "final" / filename).read_text(encoding="utf-8") for filename in reader_figure_requirements)
    check("old English-heavy figure labels absent", not any(phrase in used_svg_text for phrase in old_english_figure_phrases), [p for p in old_english_figure_phrases if p in used_svg_text])

    for value in ["29/36=80.56%", "16/19=84.21%", "LUT 9,719", "FF 5,038", "BRAM 0", "DSP 0", "8.184 ns", "1.95 LSB", "1.019633440086 V", "0.92 mV", "100.7 dB", "15/16", "21,600,000 bits"]:
        check(f"required result {value}", value in text)
    for value in ["54.01 ms", "33.3 MSPS", "33,300", "0.099 W", "5.35 mJ"]:
        check(f"unverified benchmark absent {value}", value not in text)
    check("benchmark pending", "PENDING_EXTERNAL_BENCHMARK_IMPORT" in text)
    check("validation boundary", "검증 결과 32/32=100.00%는 Final Membrane 모델 선택" in text and "최종 일반화 성능으로 승격하지 않는다" in text)
    check("equivalence not accuracy", "classifier의 정답 표지 정확도를 100%로 만들지는 않는다" in text)
    check("dataset confounding", "원천 record 단위 분할은 직접 누출을 막지만" in text.lower())
    check("physical boundary", "실제 AFE/ADC" in text and ("fabricated SoC" in text or "fabricated silicon" in text))

    metrics = json.loads((ROOT / "source_of_truth" / "global_metrics.yaml").read_text(encoding="utf-8"))
    check("global final metric", metrics["metrics"]["final_test_chunk_accuracy"]["value"] == 80.56)
    check("benchmark values remain null", all(v is None for k, v in metrics["benchmark"].items() if k != "status"))
    with (ROOT / "source_of_truth" / "claim_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        known = {row["claim_id"] for row in csv.DictReader(handle)}
    with EVIDENCE_MAP.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {"section", "statement_id", "summarized_statement", "claim_id", "evidence_path", "upstream_repository", "upstream_commit", "owner", "status", "limitation"}
    check("evidence-map schema", bool(rows) and set(rows[0]) == required_columns)
    check("evidence-map coverage", len(rows) >= 38, len(rows))
    valid_sections = {"초록", "부록"} | {str(i) for i in range(1, 8)} | {s.split()[0] for s in SUBHEADINGS}
    for row in rows:
        check(f"map section {row['statement_id']}", row["section"] in valid_sections, row["section"])
        check(f"map path {row['statement_id']}", (ROOT / row["evidence_path"]).exists(), row["evidence_path"])
        used = set(re.findall(r"CLM-\d{3}", row["claim_id"]))
        check(f"map claims {row['statement_id']}", used.issubset(known), used - known)

    inline_paths = re.findall(r"`((?:components|datasets|docs|tables|figures|source_of_truth|benchmarks|reports)/[^`]+)`", text)
    for relative in inline_paths:
        check(f"inline path {relative}", (ROOT / relative).exists())
    check("owners", all(term in text for term in ["서민우(MATLAB", "이수환(XMODEL", "양건(디지털"]))
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
