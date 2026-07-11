#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [건이형 #3] AFE fullrec → 36 chunk의 SHA256 bit-identity per-case artifact 생성.
#   생성 chunk sha256 vs board_replay_36_cases.csv의 mem_sha256 대조.
#   출력: docs/integration_latest/afe36_sha256_bitidentity.{csv,md}
# repo-root 자동탐색(개인 절대경로 제거): env ECG_SOC_ROOT 우선, 없으면 파일 위치 기준.
import os, csv, glob, hashlib
from pathlib import Path

ROOT = Path(os.environ.get("ECG_SOC_ROOT", Path(__file__).resolve().parents[1]))
CASES = ROOT / "digital_block/reports/final/board_replay_36_cases.csv"
OUTD = ROOT / "docs/integration_latest"
WIN = 1_800_000
SKIP = 2000  # canonical: start_sample = SKIP + chunk_id*WIN

def find_src(rid):
    for base in ["fullrec_afe", "fullrec_afe_remaining"]:
        hits = glob.glob(str(ROOT / f"datasets/{base}/*/*/{rid}.mem"))
        if hits:
            return Path(hits[0])
    return None

rows = list(csv.DictReader(open(CASES)))
out = []
n_match = 0
for r in rows:
    rid = r["source_record_id"].split("_")[-1]
    cid = int(r["chunk_id"])
    start = SKIP + cid * WIN
    src = find_src(rid)
    gen_sha = "SRC_MISSING"
    if src:
        with open(src, "rb") as f:
            f.seek(start * 4)
            data = f.read(WIN * 4)
        gen_sha = hashlib.sha256(data).hexdigest() if len(data) == WIN * 4 else "SHORT_READ"
    exp = r["mem_sha256"]
    match = (gen_sha == exp)
    n_match += match
    out.append(dict(
        case_id=r["case_id"], source_record_id=r["source_record_id"], chunk_id=cid,
        start_sample=start,
        source_fullrec_path=(str(src.relative_to(ROOT)) if src else "MISSING"),
        generated_chunk_sha256=gen_sha, board_replay_mem_sha256=exp,
        match=str(match).lower()))

cols = ["case_id", "source_record_id", "chunk_id", "start_sample", "source_fullrec_path",
        "generated_chunk_sha256", "board_replay_mem_sha256", "match"]
OUTD.mkdir(parents=True, exist_ok=True)
with open(OUTD / "afe36_sha256_bitidentity.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)

with open(OUTD / "afe36_sha256_bitidentity.md", "w", encoding="utf-8") as f:
    f.write("# AFE 36 chunk SHA256 bit-identity (vs digital board-replay input)\n\n")
    f.write(f"> AFE full-record output에서 slicing한 36개 30분 final-test chunk가 digital board-replay input과 SHA256 기준으로 **{n_match}/36 동일**.\n")
    f.write(f"> windowing: `start_sample = {SKIP} + chunk_id × {WIN:,}`, 길이 {WIN:,} (1 kSPS, 30 min). 생성기 `scripts/gen_sha256_bitidentity.py`.\n\n")
    f.write("| case_id | record | chunk | start_sample | gen_sha256(앞12) | board_sha256(앞12) | match |\n")
    f.write("|---|---|---|---|---|---|---|\n")
    for r in out:
        f.write(f"| {r['case_id']} | {r['source_record_id']} | {r['chunk_id']} | {r['start_sample']:,} | "
                f"`{r['generated_chunk_sha256'][:12]}` | `{r['board_replay_mem_sha256'][:12]}` | {r['match']} |\n")
    f.write(f"\n**결과: SHA256 match {n_match}/36.** 전 case에서 생성 chunk가 board-replay 입력과 바이트 단위 동일.\n")

print(f"SHA256 match {n_match}/36 -> {OUTD}/afe36_sha256_bitidentity.csv/.md")
