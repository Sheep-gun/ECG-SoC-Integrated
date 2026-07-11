#!/usr/bin/env python3
"""Fail-closed checks for the integrated Korean technical-report manuscript."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_KR.md"
CHECKLIST = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_REVIEW_CHECKLIST.md"
EVIDENCE_MAP = ROOT / "reports" / "INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv"

REQUIRED_TOP = [
    "# 초록", "# 1. 서론", "# 2. 전체 시스템 구성",
    "# 3. 데이터셋 및 평가 프로토콜", "# 4. 제안 SNN-Inspired 디지털 구조",
    "# 5. MATLAB 및 XMODEL 기반 AFE/ADC 검증", "# 6. RTL 및 FPGA 구현",
    "# 7. 실험 및 검증 결과", "# 8. 연구의 차별성 및 기술적 의의",
    "# 9. 한계 및 향후 과제", "# 10. 결론", "# 참고문헌",
    "# 부록 A. 핵심 수치 표", "# 부록 B. Claim 및 evidence 추적",
]

REQUIRED_SUB = [
    "1.1 연구 배경", "1.2 기존 ECG screening 범위와 문제 인식", "1.3 장시간 ECG 분석의 필요성",
    "1.4 연구 목표", "1.5 연구 범위와 기여",
    "2.1 End-to-end processing flow", "2.2 MATLAB nominal AFE+ADC pre-validation",
    "2.3 SystemVerilog XMODEL AFE+ADC verification", "2.4 Signed 12-bit digital handoff",
    "2.5 Digital SNN-inspired accelerator", "2.6 FPGA/IP integration flow",
    "3.1 NSR, CHF, ARR, AFF source databases", "3.2 1 kSPS signed 12-bit stream generation",
    "3.3 60-second Snapshot dataset", "3.4 30-minute chunk and source-record organization",
    "3.5 Strict source-record-wise split", "3.6 Model selection and final-test lock",
    "3.7 Evaluation metrics", "3.8 Database–class confounding",
    "4.1 설계 철학", "4.2 Adaptive event encoder", "4.3 QRS LIF / beat detection",
    "4.4 RR timing and PNN rhythm prediction", "4.5 RDM variability evidence",
    "4.6 DSCR morphology evidence", "4.7 R-peak amplitude evidence",
    "4.8 Ectopic-like pair evidence", "4.9 QRS morphology and delay evidence",
    "4.10 Snapshot class readout", "4.11 Final Membrane accumulation",
    "4.12 Guard, rescue, veto, and silent-AFF logic", "4.13 Final WTA decision",
    "4.14 SNN-inspired라는 표현의 범위",
    "5.1 Nominal analog-chain intent", "5.2 Frequency response and gain",
    "5.3 ADC range, clipping, and headroom", "5.4 Signed two’s-complement reference vectors",
    "5.5 Emulator–XMODEL waveform agreement", "5.6 PLI, baseline wander, offset, and mismatch",
    "5.7 Op-amp and ADC non-ideal stress", "5.8 AFE-generated long-stream handoff",
    "5.9 Model-based verification의 해석 범위",
    "6.1 RTL architecture", "6.2 Streaming state and memory structure",
    "6.3 Top-level FSM and decision flow", "6.4 Pure RTL implementation",
    "6.5 AXI/IP-XACT packaging", "6.6 Vitis/MicroBlaze replay system",
    "6.7 FPGA board replay procedure", "6.8 Classification accuracy와 functional equivalence의 구분",
    "7.1 Train and validation results", "7.2 Locked final-test chunk result",
    "7.3 Record-majority result", "7.4 Class-wise confusion analysis",
    "7.5 MATLAB nominal results", "7.6 XMODEL waveform/stress results",
    "7.7 AFE input SHA256 identity", "7.8 Canonical AFE-to-RTL equivalence",
    "7.9 FPGA board equivalence", "7.10 Hardware resource and timing-closure result",
    "7.11 Accelerator benchmark status",
    "8.1 Four-class long-window engineering target", "8.2 Multi-timescale temporal hierarchy",
    "8.3 SNN-inspired event/state realization", "8.4 Full-window buffering을 요구하지 않는 streaming structure",
    "8.5 Mixed-signal-to-digital traceability", "8.6 RTL/IP/FPGA implementation completeness",
    "8.7 Reproducible evidence and claim control",
    "9.1 Database–class confounding", "9.2 Dataset size and clinical generalization",
    "9.3 Physical AFE/ADC and fabricated-silicon gap", "9.4 SNN-inspired architecture의 한계",
    "9.5 Snapshot/Final Membrane ablation 필요성", "9.6 Independent accelerator benchmark",
    "9.7 Same-acquisition multi-class validation", "9.8 향후 ASIC 및 edge-device 확장",
]

REQUIRED_FIGURES = [
    "FIG-01_long_window_motivation.svg", "FIG-02_complete_system_flow.svg",
    "FIG-04_multitimescale_architecture.svg", "FIG-05_strict_recordwise_protocol.svg",
    "FIG-06_matlab_nominal_summary.svg", "FIG-07_xmodel_scope.svg",
    "FIG-08_signed_stream_handoff.svg", "FIG-09_digital_validation_hierarchy.svg",
    "FIG-10_classification_summary.svg", "FIG-11_confounding_claim_boundary.svg",
]


def main() -> int:
    failures: list[str] = []
    checked: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checked.append(name)
        if not ok:
            failures.append(f"{name}: {detail or 'failed'}")

    for path in [REPORT, CHECKLIST, EVIDENCE_MAP]:
        check(f"required output exists: {path.name}", path.is_file())
    if not REPORT.exists():
        return 1

    text = REPORT.read_text(encoding="utf-8-sig")
    check("substantive manuscript length", 15_000 <= len(text) <= 60_000, str(len(text)))
    for heading in REQUIRED_TOP:
        check(f"top heading: {heading}", heading in text)
    for heading in REQUIRED_SUB:
        check(f"subheading: {heading}", f"## {heading}" in text)

    metrics = json.loads((ROOT / "source_of_truth" / "global_metrics.yaml").read_text(encoding="utf-8"))
    expected_strings = [
        "61/68=89.71%", "32/32=100.00%", "29/36=80.56%", "80.44%",
        "16/19=84.21%", "80.80%", "1.0196 V", "1.95 LSB",
        "LUT 9,719", "FF 5,038", "BRAM 0", "DSP 0", "8.184 ns",
        "LUT 12,494", "register 8,494", "BRAM 16", "DSP 3", "0.097 ns",
        "sample_gap_cycles=2", "PENDING_EXTERNAL_BENCHMARK_IMPORT",
    ]
    for value in expected_strings:
        check(f"promoted value present: {value}", value in text)
    check("global final metric exact", metrics["metrics"]["final_test_chunk_accuracy"]["value"] == 80.56)
    check("global benchmark nulls", all(v is None for k, v in metrics["benchmark"].items() if k != "status"))

    for figure in REQUIRED_FIGURES:
        check(f"figure referenced: {figure}", figure in text)
        check(f"figure exists: {figure}", (ROOT / "figures" / "final" / figure).is_file())
    check("at least ten report captions", text.count("*그림 ") >= 10, str(text.count("*그림 ")))
    check("at least ten report tables", text.count("*표 ") >= 10, str(text.count("*표 ")))

    with EVIDENCE_MAP.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {"section", "statement_id", "summarized_statement", "claim_id", "evidence_path", "upstream_repository", "upstream_commit", "owner", "status", "limitation"}
    check("evidence-map columns", bool(rows) and set(rows[0]) == required_columns)
    check("evidence-map coverage", len(rows) >= 25, str(len(rows)))
    for row in rows:
        check(f"evidence path exists: {row['statement_id']}", (ROOT / row["evidence_path"]).exists(), row["evidence_path"])

    with (ROOT / "source_of_truth" / "claim_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
        claims = list(csv.DictReader(handle))
    known_claims = {row["claim_id"] for row in claims}
    used_claims = set(re.findall(r"CLM-\d{3}", text + EVIDENCE_MAP.read_text(encoding="utf-8-sig")))
    check("all used claim IDs registered", used_claims.issubset(known_claims), str(sorted(used_claims-known_claims)))

    ownership = (ROOT / "source_of_truth" / "ownership_matrix.csv").read_text(encoding="utf-8-sig")
    check("MATLAB owner correct", "서민우" in text and "MATLAB" in ownership)
    check("XMODEL owner correct", "이수환" in text and "XMODEL" in ownership)
    check("digital owner correct", "양건" in text and "Project leader" in ownership)

    check("validation bounded", "validation 100%를 final generalization result로 보고하지 않는다" in text)
    check("board accuracy separated", "functional equivalence이며, ground-truth label 기준 분류 정확도 100%를 의미하지 않는다" in text)
    check("confounding explicit", "record-wise split은 direct leakage를 막지만" in text.lower() and "database-specific acquisition" in text.lower())
    check("physical boundary explicit", "physical mixed-signal SoC를 의미하지 않는다" in text and "fabricated SoC" in text)
    check("SNN-inspired boundary explicit", all(term in text for term in ["backpropagation-through-time", "STDP", "online learning", "biophysical equivalence"]))
    check("streaming raw-storage equation", all(term in text for term in ["21,600,000 bits", "2,700,000 bytes", "2.7 MB"]), "missing storage calculation")

    forbidden_benchmark = ["54.01 ms", "33.3 MSPS", "33,300", "0.099 W", "5.35 mJ"]
    for value in forbidden_benchmark:
        check(f"forbidden benchmark absent: {value}", value not in text)
    check("pending table repeated", text.count("Pending independent benchmark import") >= 5)

    refs_text = (ROOT / "source_of_truth" / "external_reference_registry.csv").read_text(encoding="utf-8-sig")
    report_urls = re.findall(r"https?://[^\s)]+", text[text.index("# 참고문헌"):text.index("# 부록 A")])
    check("six registered references", len(report_urls) == 6, str(report_urls))
    for url in report_urls:
        check(f"reference registered: {url}", url in refs_text)

    check("no private email", re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I) is None)
    check("no personal absolute path", re.search(r"[A-Z]:[\\/]Users[\\/]", text, re.I) is None)
    check("no Korean phone pattern", re.search(r"01[016789][- ]?\d{3,4}[- ]?\d{4}", text) is None)
    check("no student-id field", "학번:" not in text and "student id:" not in text.lower())

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    evidence_doc = (ROOT / "docs" / "REPORT_EVIDENCE_MAP_KR.md").read_text(encoding="utf-8")
    check("README links completed manuscript", "reports/INTEGRATED_TECHNICAL_REPORT_KR.md" in readme)
    check("official HWP distinguished", "향후 official private HWP/application form" in evidence_doc)

    print(f"{'PASS' if not failures else 'FAIL'}: {len(checked)} report rules, {len(failures)} conflicts, chars={len(text)}, claims={len(used_claims)}")
    if failures:
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
