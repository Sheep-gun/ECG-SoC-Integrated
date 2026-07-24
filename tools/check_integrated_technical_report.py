#!/usr/bin/env python3
"""Fail-closed checks for the public integrated technical report."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/INTEGRATED_TECHNICAL_REPORT_KR.md"
EVIDENCE = ROOT / "reports/INTEGRATED_TECHNICAL_REPORT_EVIDENCE_MAP.csv"
CLAIMS = ROOT / "project_registry/claim_registry.csv"

REQUIRED_HEADINGS = [
    "# 1. 연구 목적과 필요성",
    "# 2. 관련 연구와 설계 위치",
    "# 3. 데이터 구성과 평가 protocol",
    "# 4. 시스템과 알고리즘",
    "# 5. RTL/IP와 FPGA 구현",
    "# 6. 검증",
    "# 7. 분류 결과",
    "# 8. RTL timing bottleneck 해결",
    "# 9. 가속 성능과 전력",
    "# 10. 기여와 한계",
    "# 11. 재현성과 저장소 구조",
    "# 참고문헌",
]
REQUIRED_TEXT = [
    "80.56%", "80.44%", "9,719", "5,038", "8.184 ns",
    "12,494", "8,494", "0.097 ns", "36.0129 ms", "49.36",
    "142.0 mW", "2.991 µW", "database–class confounding", "30분", "24시간",
    "c6b80de19cdcad5b7e43fe7835588b629d847f75",
    "c7c75cfebf7add12bfcc32bb59d5edf38ac6e5aa",
    "5e2e5d0a46be47d8086b8642e055066079bfa4e6",
]
FORBIDDEN = [
    "SNN-inspired", "본 연구는 세계 최초", "동일한 연구가 없음을 확인",
    "실측 소비전력 2.991", "FPGA 소비전력은 2.991", "임상적으로 검증",
]


def main() -> int:
    errors: list[str] = []
    text = REPORT.read_text(encoding="utf-8")
    for item in REQUIRED_HEADINGS:
        if item not in text:
            errors.append(f"missing heading: {item}")
    for item in REQUIRED_TEXT:
        if item not in text:
            errors.append(f"missing required statement/token: {item}")
    for item in FORBIDDEN:
        if item in text:
            errors.append(f"forbidden wording: {item}")
    if "이는 세계 최초 또는 동일 연구가 없다는 단정이 아니다" not in text:
        errors.append("missing explicit novelty limitation")

    with CLAIMS.open(encoding="utf-8", newline="") as handle:
        claim_ids = {row["claim_id"] for row in csv.DictReader(handle)}
    with EVIDENCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        errors.append("evidence map is empty")
    for row in rows:
        if row["claim_id"] not in claim_ids:
            errors.append(f"unknown claim id in evidence map: {row['claim_id']}")
        if not (ROOT / row["evidence_path"]).exists():
            errors.append(f"missing evidence path: {row['evidence_path']}")

    ref_count = sum(1 for line in text.splitlines() if line[:1].isdigit() and ". " in line[:4])
    if ref_count < 8:
        errors.append(f"expected at least 8 numbered references; found {ref_count}")

    if errors:
        print("INTEGRATED_REPORT: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("INTEGRATED_REPORT: PASS")
    print(f"- {len(rows)} evidence-map rows resolved")
    print(f"- {ref_count} numbered references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
