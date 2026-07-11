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

MAIN_HEADINGS = [
    "# 1. 서론",
    "# 2. 전체 시스템과 평가 방법",
    "# 3. 제안 SNN-Inspired 디지털 아키텍처",
    "# 4. MATLAB/XMODEL 및 FPGA 구현",
    "# 5. 실험 결과",
    "# 6. 종합 논의와 한계",
    "# 7. 결론",
]
SUBHEADINGS = [
    "1.1 연구 배경과 문제 정의", "1.2 연구 목표와 주요 기여",
    "2.1 신호 처리 및 구현 흐름", "2.2 데이터셋과 평가 프로토콜",
    "3.1 핵심 개념과 다중 시간축 처리", "3.2 박동 및 리듬 정보 추출",
    "3.3 파형 형태 및 진폭 정보 추출", "3.4 60초 Snapshot과 30분 Final Membrane",
    "3.5 Streaming state와 하드웨어 구현 방식",
    "4.1 AFE·ADC 모델 검증", "4.2 RTL/IP/FPGA 구현", "4.3 End-to-end 기능 등가성 검증",
    "5.1 분류 성능", "5.2 Mixed-signal 및 디지털 통합 결과", "5.3 하드웨어 구현 결과",
    "6.1 설계적 차별성과 기술적 의의", "6.2 결과의 해석 범위와 향후 과제",
]
REQUIRED_FILES = [REPORT, CHECKLIST, EVIDENCE_MAP]
REQUIRED_FIGURES = [
    "FIG-01_long_window_motivation.svg", "FIG-02_complete_system_flow.svg",
    "FIG-04_multitimescale_architecture.svg", "FIG-08_signed_stream_handoff.svg",
    "FIG-10_classification_summary.svg", "FIG-12_detailed_digital_architecture.svg",
    "FIG-13_beat_rhythm_path.svg", "FIG-14_morphology_path.svg",
]
MECHANISM_TERMS = [
    "previous_sample_next", "old `qrs_mem`", "refractory_old", "46개 hypothesis center",
    "abs(current_rr-prev_rr)", "early→late", "filter_update", "prev_slope_sign",
    "ram_window_open", "최대 amplitude code", "박동 전 120표본", "박동 후 100표본",
    "width proxy", "Complexity", "Pre-QRS activity", "activity onset", "terminal window",
    "repeated", "*_count_next", "Base seed", "guard", "rescue", "veto", "silent-AFF",
    "strict `>`", "IDLE→CORE_RESET→SEG_START→RUN→SEG_DONE→FLUSH→COMMIT→DONE",
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

    primer = section(text, "3.1 핵심 개념과 다중 시간축 처리", 2)
    for term in ["표본값(sample)", "사건 신호(event)", "막전위형 상태(membrane state)", "누설(leak)", "문턱값(threshold)", "불응기(refractory", "박동(beat)", "RR interval", "Snapshot", "Final Membrane"]:
        check(f"concept defined {term}", term in primer)
    check("concepts precede module detail", text.index("**표본값(sample).**") < text.index("ecg_event_encoder_adaptive"))
    check("running signal example", all(token in text for token in ["+  →  +  →  -", "+  →  +  →  +", "비임상 설명 예"]))
    for term in MECHANISM_TERMS:
        check(f"mechanism {term}", term.lower() in text.lower())
    for block in ["ecg_event_encoder_adaptive", "qrs_lif_detector", "pnn_rhythm_predictor", "rdm_variability_neuron", "ectopic_pair_neuron", "dscr_spike_counter", "ram_peak_accumulator", "qrs_maf_neuron", "rbbb_qrs_delay_bank", "class_score_neurons", "final_membrane_layer"]:
        check(f"direct RTL block {block}", block in text)
    check("locked QRS leak nuance", "QRS leak 값은 0" in text)
    check("SNN boundary", all(term in text for term in ["trained deep SNN", "STDP", "online learning", "biophysical neuron simulation"]))

    report_images = re.findall(r"!\[[^]]*\]\(([^)]+)\)", text)
    check("eight reader-facing figures", len(report_images) == 8, len(report_images))
    for filename in REQUIRED_FIGURES:
        matches = [p for p in report_images if Path(p).name == filename]
        check(f"figure referenced {filename}", len(matches) == 1, matches)
        check(f"figure exists {filename}", (ROOT / "figures" / "final" / filename).is_file())
    figure12 = (ROOT / "figures" / "final" / "FIG-12_detailed_digital_architecture.svg").read_text(encoding="utf-8")
    for label in ["입력 ECG 표본값", "파형 변화 사건", "박동 검출", "박동 간격 측정", "리듬 분석", "60초 증거 누적", "30분 class 상태", "최종 class 선택"]:
        check(f"FIG-12 Korean label {label}", label in figure12)

    for value in ["29/36=80.56%", "16/19=84.21%", "LUT 9,719", "FF 5,038", "BRAM 0", "DSP 0", "8.184 ns", "1.95 LSB", "1.019633440086 V", "0.92 mV", "100.7 dB", "15/16", "21,600,000 bits"]:
        check(f"required result {value}", value in text)
    for value in ["54.01 ms", "33.3 MSPS", "33,300", "0.099 W", "5.35 mJ"]:
        check(f"unverified benchmark absent {value}", value not in text)
    check("benchmark pending", "PENDING_EXTERNAL_BENCHMARK_IMPORT" in text)
    check("validation boundary", "Validation 32/32=100.00%는 Final Membrane model selection" in text and "final generalization으로 승격하지 않는다" in text)
    check("equivalence not accuracy", "classifier의 label accuracy를 100%로 만들지 않는다" in text)
    check("dataset confounding", "record-wise split은 direct leakage를 막지만" in text.lower())
    check("physical boundary", "physical AFE/ADC" in text and ("fabricated SoC" in text or "fabricated silicon" in text))

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
    check("owners", all(term in text for term in ["서민우(MATLAB", "이수환(XMODEL", "양건(digital"]))
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
