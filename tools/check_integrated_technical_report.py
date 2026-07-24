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
    "# I. 설계작품 요약서",
    "# II. 설계결과물 설명서",
    "## 1. 설계 개요",
    "## 2. 설계기술 설명서",
    "### 2.1 설계 목표",
    "### 2.2 알고리즘 구성 및 결과(예상)",
    "### 2.3 설계회로 구성",
    "### 2.4 설계회로 검증",
    "### 2.5 설계회로 구현 결과",
    "### 2.6 목표 대비 결과 비교",
    "# III. 제품 및 기술요약",
    "# IV. 보고서 외 추가 기술기록",
    "## A. annotation 기반 사전 특징 선정",
    "## B. RTL timing 병목과 파이프라인 최적화",
    "## C. 관련 연구의 확장 기록",
    "## D. 재현성과 주장 범위",
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
REQUIRED_VERBATIM_EXCERPTS = [
    "대표적인 ECG 검사인 Holter 검사가 24~48시간 이상 심전도를 기록하는 것도 간헐적으로 나타나는 이상을 포착하기 위해서이다.",
    "이에 본 작품은 분류에 필요한 사건, 리듬 및 파형 증거만 순차적으로 누적하는 SNN 기반 저전력 스트리밍 구조를 채택하였다.",
    "따라서 30분은 하드웨어의 처리 한계가 아니라 공개 데이터셋을 공정하게 비교하기 위한 표준 평가 단위이다.",
    "분류 구조의 가중치와 임계값은 학습 및 검증 데이터로 결정하고 RTL로 구현한 뒤 최종 시험 전에 고정하였다.",
    "현재 개발 범위는 모델 기반 AFE–ADC와 FPGA 디지털 IP의 통합 설계 및 검증 단계이며, ASIC 제작과 post-layout 검증은 후속 과제이다.",
    "원시 ECG 전체를 저장하지 않고, 표본이 입력될 때마다 사건을 검출하고 뉴런의 증거 누적값을 순차적으로 갱신하는 스트리밍 구조이다.",
    "현재 표본과 직전 표본의 차이인 ΔECG를 구하고, 그 절댓값이 구간 초기의 입력 변화에 맞춰 자동 설정된 문턱값을 넘으면 부호에 따라 상승 또는 하강 Strong Event를 발생시킨다.",
    "Pure RTL은 AXI IP로 패키징하였다.",
    "분류 성능은 학습/검증 데이터와 원천 record가 겹치지 않고 모델 선택에도 사용되지 않은 fully held-out 최종 시험 데이터로, 설계 고정 후 최초 한 번만 평가하였다.",
    "다만 장시간 처리와 저전력 목표는 각각 30분 입력 검증과 이상적인 power-gating 조건의 산출값에 근거하므로 조건부 달성으로 평가하였다.",
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
    for item in REQUIRED_VERBATIM_EXCERPTS:
        if item not in text:
            errors.append(f"missing submission verbatim excerpt: {item}")
    for item in FORBIDDEN:
        if item in text:
            errors.append(f"forbidden wording: {item}")
    if "문장과 표현 그대로 옮긴 것이다" not in text:
        errors.append("missing submission-source verbatim preservation notice")
    if "PDF에 없는 설명은 본문과 섞지 않고" not in text:
        errors.append("missing separation between submission text and supplemental record")
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
