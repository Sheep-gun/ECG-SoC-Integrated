#!/usr/bin/env python3
"""Fail-closed quality, evidence, and claim checks for the definitive report."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_KR.md"
CHECKLIST = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_REVIEW_CHECKLIST.md"
EVIDENCE_MAP = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv"

REQUIRED_TOP = [
    "# 초록", "# 핵심어", "# 1. 서론", "# 2. 전체 시스템 구성",
    "# 3. 데이터셋 및 평가 방법", "# 4. 제안 SNN-Inspired 디지털 구조",
    "# 5. MATLAB 및 XMODEL 기반 AFE/ADC 검증", "# 6. RTL 및 FPGA 구현",
    "# 7. 실험 결과", "# 8. 종합 논의", "# 9. 창의성·기술성·완성도",
    "# 10. 한계 및 향후 과제", "# 11. 결론", "# 참고문헌",
    "# 부록 A. 핵심 수치 표", "# 부록 B. Claim 및 evidence 추적",
    "# 부록 C. 주요 artifact 및 재현 절차",
]

REQUIRED_SUB = [
    "1.1 연구 배경", "1.2 기존 기능 범위와 문제 정의", "1.3 장시간 ECG 분석의 공학적 필요성",
    "1.4 연구 목표", "1.5 주요 기여", "1.6 연구 범위",
    "2.1 End-to-end signal and evidence flow", "2.2 MATLAB nominal AFE+ADC pre-validation",
    "2.3 SystemVerilog XMODEL AFE+ADC verification", "2.4 Signed 12-bit digital interface",
    "2.5 SNN-inspired digital accelerator", "2.6 RTL/IP/FPGA integration",
    "2.7 Contributor ownership and handoff",
    "3.1 Source databases", "3.2 Dataset license and reproducible retrieval",
    "3.3 Common 1 kSPS signed 12-bit conversion", "3.4 60-second Snapshot construction",
    "3.5 30-minute chunk construction", "3.6 Source-record-wise split",
    "3.7 Model selection and final-test lock", "3.8 Evaluation metrics",
    "3.9 Database–class confounding",
    "4.1 설계 철학", "4.2 Adaptive event encoder", "4.3 QRS LIF detector",
    "4.4 Beat/RR timing", "4.5 PNN rhythm predictor", "4.6 RDM variability",
    "4.7 DSCR morphology", "4.8 RAM peak evidence", "4.9 Ectopic-pair evidence",
    "4.10 QRS MAF evidence", "4.11 RBBB-like delay evidence", "4.12 Snapshot class readout",
    "4.13 Final Membrane accumulation", "4.14 Guard/rescue/veto/silent-AFF",
    "4.15 Final WTA", "4.16 SNN-inspired claim boundary",
    "5.1 Nominal analog-chain intent", "5.2 Frequency and gain response",
    "5.3 ADC range, clipping and headroom", "5.4 Reference-vector package",
    "5.5 Emulator–XMODEL waveform agreement", "5.6 PLI and baseline stress",
    "5.7 Component mismatch", "5.8 Op-amp and ADC non-ideal stress",
    "5.9 Long-record signed-stream generation", "5.10 Model-based verification boundary",
    "6.1 RTL datapath", "6.2 Streaming persistent-state structure", "6.3 Top-level FSM",
    "6.4 Snapshot and final-decision control", "6.5 Pure RTL implementation",
    "6.6 AXI/IP-XACT packaging", "6.7 Vitis/MicroBlaze replay system",
    "6.8 FPGA replay", "6.9 Accuracy and equivalence separation",
    "7.1 Train and validation", "7.2 Locked final-test chunk result",
    "7.3 Record-majority result", "7.4 Class-wise confusion analysis",
    "7.5 MATLAB nominal result", "7.6 XMODEL result", "7.7 AFE input SHA256 identity",
    "7.8 Canonical AFE-to-RTL equivalence", "7.9 FPGA functional equivalence",
    "7.10 Hardware resource and timing closure", "7.11 Streaming-memory evidence",
    "7.12 Accelerator benchmark status",
    "8.1 Classification result interpretation", "8.2 Multi-timescale architecture significance",
    "8.3 SNN-inspired realization significance", "8.4 Hardware implementation significance",
    "8.5 Mixed-signal-to-digital traceability", "8.6 Reproducibility and evidence control",
    "8.7 Comparison scope and claim boundaries",
    "9.1 설계적 차별성", "9.2 기술적 난이도", "9.3 구현 완결성", "9.4 검증 완결성",
    "9.5 대회 평가 관점의 핵심 가치",
    "10.1 Database–class confounding", "10.2 Dataset support and generalization",
    "10.3 Snapshot/Final Membrane ablation", "10.4 Physical AFE/ADC validation",
    "10.5 ASIC/post-layout validation", "10.6 Clinical validation",
    "10.7 Exact C++ CPU baseline", "10.8 Accelerator-benefit benchmark",
    "10.9 Board latency and power", "10.10 Same-acquisition multi-class validation",
]

REQUIRED_FIGURES = [f"FIG-{index:02d}_" for index in range(1, 13)]
REQUIRED_BLOCKS = [
    "ecg_event_encoder_adaptive", "qrs_lif_detector", "pnn_rhythm_predictor",
    "rdm_variability_neuron", "dscr_spike_counter", "ram_peak_accumulator",
    "ectopic_pair_neuron", "qrs_maf_neuron", "rbbb_qrs_delay_bank",
    "class_score_neurons", "final_membrane_layer", "silent-AFF", "winner-take-all",
]


def section_body(text: str, heading: str, level: int = 2) -> str:
    marker = f"{'#' * level} {heading}"
    start = text.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    pattern = rf"(?m)^#{{1,{level}}} "
    next_heading = re.search(pattern, text[start:])
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end].strip()


def main() -> int:
    failures: list[str] = []
    checked: list[str] = []

    def check(name: str, ok: bool, detail: object = "") -> None:
        checked.append(name)
        if not ok:
            failures.append(f"{name}: {detail or 'failed'}")

    for path in [REPORT, CHECKLIST, EVIDENCE_MAP]:
        check(f"required output exists: {path.name}", path.is_file())
    if not REPORT.is_file():
        return 1

    text = REPORT.read_text(encoding="utf-8-sig")
    check("award-paper manuscript length", 25_000 <= len(text) <= 40_000, len(text))
    for heading in REQUIRED_TOP:
        check(f"top heading: {heading}", heading in text)
    for heading in REQUIRED_SUB:
        check(f"subheading: {heading}", f"## {heading}" in text)
        body = section_body(text, heading)
        prose = re.sub(r"!\[[^]]*\]\([^)]*\)|\|.*\||[*`#]", "", body)
        check(f"subsection substantive: {heading}", len(prose.strip()) >= 35, len(prose.strip()))

    abstract = section_body(text, "초록", level=1)
    check("abstract length 900-1300", 900 <= len(abstract) <= 1_300, len(abstract))
    abstract_terms = [
        "NSR", "CHF", "ARR", "AFF", "signed 12-bit", "1 kSPS", "Snapshot",
        "Final Membrane", "SNN-inspired", "source-record-wise", "29/36=80.56%",
        "16/19=84.21%", "LUT 9,719", "FF 5,038", "BRAM 0", "DSP 0",
        "36/36", "1,800,000-sample", "confounding", "모델 기반",
        "PENDING_EXTERNAL_BENCHMARK_IMPORT",
    ]
    for term in abstract_terms:
        check(f"abstract contains: {term}", term in abstract)

    keywords = section_body(text, "핵심어", level=1).splitlines()[0]
    keyword_items = [item.strip() for item in keywords.split(",") if item.strip()]
    check("five to eight keywords", 5 <= len(keyword_items) <= 8, keyword_items)

    contributions = section_body(text, "1.5 주요 기여")
    for number in range(1, 7):
        check(f"explicit contribution {number}", re.search(rf"(?m)^{number}\. ", contributions) is not None)

    conclusion = section_body(text, "11. 결론", level=1)
    check("substantive conclusion", len(conclusion) >= 900, len(conclusion))
    check("discussion substantive", len(section_body(text, "8. 종합 논의", level=1)) >= 1_500)
    check("judge chapter substantive", len(section_body(text, "9. 창의성·기술성·완성도", level=1)) >= 800)

    for block in REQUIRED_BLOCKS:
        check(f"important architecture block: {block}", block in text)

    report_images = re.findall(r"!\[[^]]*\]\(([^)]+)\)", text)
    check("twelve report figures referenced", len(report_images) == 12, len(report_images))
    for prefix in REQUIRED_FIGURES:
        matches = [path for path in report_images if Path(path).name.startswith(prefix)]
        check(f"figure family referenced: {prefix}", len(matches) == 1, matches)
    for relative in report_images:
        resolved = (REPORT.parent / relative).resolve()
        check(f"figure exists: {Path(relative).name}", resolved.is_file(), resolved)
    check("twelve figure captions", text.count("*그림 ") == 12, text.count("*그림 "))

    for number in range(1, 15):
        caption = f"*표 {number}."
        check(f"report table caption {number}", caption in text)
        if caption in text:
            pos = text.index(caption)
            tail = text[pos + len(caption):]
            boundary = re.search(r"(?m)^(?:## |\|[^\n]+\|\s*$|\*표 )", tail)
            interpretation = tail[:boundary.start()] if boundary else tail[:900]
            prose = re.sub(r"[*`\[\]()#]", "", interpretation).strip()
            check(f"table {number} interpretation", len(prose) >= 25, len(prose))
    check("at least fourteen report tables", text.count("*표 ") >= 14, text.count("*표 "))

    metrics = json.loads((ROOT / "source_of_truth" / "global_metrics.yaml").read_text(encoding="utf-8"))
    check("global final metric exact", metrics["metrics"]["final_test_chunk_accuracy"]["value"] == 80.56)
    check("global benchmark nulls", all(v is None for k, v in metrics["benchmark"].items() if k != "status"))

    promoted_claims = {
        "29/36=80.56%": "CLM-004", "16/19=84.21%": "CLM-005",
        "LUT 9,719": "CLM-008", "8.184 ns": "CLM-009", "LUT 12,494": "CLM-010",
        "1.95 LSB": "CLM-014", "1.019633440086 V": "CLM-024",
        "0.92 mV": "CLM-025", "100.7 dB": "CLM-026", "15/16": "CLM-027",
        "21,600,000 bits": "CLM-023",
    }
    for value, claim in promoted_claims.items():
        check(f"promoted number present: {value}", value in text)
        check(f"promoted number has claim: {claim}", claim in text)

    with (ROOT / "source_of_truth" / "claim_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        claims = list(csv.DictReader(handle))
    known_claims = {row["claim_id"] for row in claims}
    used_claims = set(re.findall(r"CLM-\d{3}", text + EVIDENCE_MAP.read_text(encoding="utf-8-sig")))
    check("all used claim IDs registered", used_claims.issubset(known_claims), sorted(used_claims - known_claims))
    for claim in ["CLM-024", "CLM-025", "CLM-026", "CLM-027"]:
        check(f"new numeric claim registered: {claim}", claim in known_claims)

    with EVIDENCE_MAP.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {
        "section", "statement_id", "summarized_statement", "claim_id", "evidence_path",
        "upstream_repository", "upstream_commit", "owner", "status", "limitation",
    }
    check("evidence-map columns", bool(rows) and set(rows[0]) == required_columns)
    check("evidence-map coverage", len(rows) >= 38, len(rows))
    for row in rows:
        check(f"evidence path exists: {row['statement_id']}", (ROOT / row["evidence_path"]).exists(), row["evidence_path"])
        mapped = set(re.findall(r"CLM-\d{3}", row["claim_id"]))
        check(f"evidence-map claim valid: {row['statement_id']}", mapped.issubset(known_claims), mapped - known_claims)

    inline_paths = re.findall(r"`((?:components|datasets|docs|tables|figures|source_of_truth|benchmarks|reports)/[^`]+)`", text)
    for relative in inline_paths:
        check(f"inline evidence path exists: {relative}", (ROOT / relative).exists(), relative)

    ownership = (ROOT / "source_of_truth" / "ownership_matrix.csv").read_text(encoding="utf-8-sig")
    check("MATLAB owner correct", "서민우(MATLAB" in text and "서민우" in ownership)
    check("XMODEL owner correct", "이수환(XMODEL" in text and "이수환" in ownership)
    check("digital owner correct", "양건(digital" in text and "양건" in ownership)

    check("validation bounded", "validation 100%를 final generalization result로 보고하지 않는다" in text)
    check("board accuracy separated", "functional equivalence이며, ground-truth label 기준 분류 정확도 100%를 의미하지 않는다" in text)
    check("confounding explicit", "record-wise split은 direct leakage를 막지만" in text.lower())
    check("physical boundary explicit", "physical mixed-signal SoC를 의미하지 않는다" in text and "fabricated SoC" in text)
    check("SNN-inspired boundary", all(term in text for term in ["backpropagation-through-time", "STDP", "online learning", "biophysical equivalence"]))
    check("streaming equation", all(term in text for term in ["21,600,000 bits", "2,700,000 bytes", "2.7 MB"]))
    check("streaming inventory cited", "tables/streaming_state_inventory.csv" in text)
    check("dataset reconstruction cited", all(term.lower() in text.lower() for term in ["datasets/dataset_manifest.yaml", "datasets/DATASET_LICENSES.md", "raw waveform", "번들하지 않는다"]))

    forbidden_benchmark = ["54.01 ms", "33.3 MSPS", "33,300", "0.099 W", "5.35 mJ"]
    for value in forbidden_benchmark:
        check(f"forbidden benchmark absent: {value}", value not in text)
    check("pending benchmark rows", text.count("Pending independent benchmark import") >= 5)
    check("WNS separated from latency", "WNS는 latency가 아니다" in text or "WNS는 processing latency가 아니다" in text)
    check("FPGA equivalence separated from accuracy", "Label accuracy는 29/36" in text and "기능 등가성" in text)

    unsupported = ["상용 wearable보다 우수", "임상적으로 우수", "silicon-proven result", "본 설계는 fabricated low-power SoC"]
    for phrase in unsupported:
        check(f"unsupported commercial wording absent: {phrase}", phrase not in text)

    refs_text = (ROOT / "source_of_truth" / "external_reference_registry.csv").read_text(encoding="utf-8-sig")
    references = section_body(text, "참고문헌", level=1)
    report_urls = re.findall(r"https?://[^\s)]+", references)
    check("eight registered references", len(report_urls) == 8, report_urls)
    for url in report_urls:
        check(f"reference registered: {url}", url in refs_text)

    check("no private email", re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I) is None)
    check("no personal absolute path", re.search(r"[A-Z]:[\\/]Users[\\/]", text, re.I) is None)
    check("no Korean phone", re.search(r"(?<!\d)01[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)", text) is None)
    check("no student-id field", "학번:" not in text and "student id:" not in text.lower())

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    title_end = readme.find("\n", readme.find("# "))
    link_pos = readme.find("## 최종 통합 기술보고서")
    identity_pos = readme.find("## 1. 프로젝트 정체성")
    check("README report block immediately after title", title_end < link_pos < identity_pos and link_pos - title_end < 5)
    check("README report link exact", "[최종 통합 기술보고서 핵심 원고 보기](reports/INTEGRATED_TECHNICAL_REPORT_KR.md)" in readme)

    print(f"{'PASS' if not failures else 'FAIL'}: {len(checked)} report rules, {len(failures)} conflicts, chars={len(text)}, abstract={len(abstract)}, conclusion={len(conclusion)}, claims={len(used_claims)}")
    if failures:
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
