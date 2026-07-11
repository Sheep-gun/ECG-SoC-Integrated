#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [1.5 확장] 우리 fullrec_afe에서 36개 30분 chunk 생성 + sha256로 팀원 chunk와 bit-identity 검증.
#  windowing(팀원 manifest): start_sample = SKIP + chunk_id*1,800,000, 길이 1,800,000
#  .mem 포맷 고정 'xxx\n'(4 byte/line) → byte-seek 고속 슬라이스.
#  사용: python3 gen_30min_chunks.py [SKIP]   (기본 2000)
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, sys, csv, glob, hashlib
ECG = _ROOT + ""
CASES = ECG + "/digital_block/reports/final/board_replay_36_cases.csv"
OUT = ECG + "/sim_out/chunks36"
WIN = 1_800_000
SKIP = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
os.makedirs(OUT, exist_ok=True)

# record_id -> source fullrec .mem 경로
def find_src(rid):
    for base in ["fullrec_afe", "fullrec_afe_remaining"]:
        hits = glob.glob(f"{ECG}/datasets/{base}/*/*/{rid}.mem")
        if hits:
            return hits[0]
    return None

rows = list(csv.DictReader(open(CASES)))
print(f"SKIP={SKIP}  cases={len(rows)}", flush=True)
match = 0; miss = []
manifest = []
for r in rows:
    rid = r["source_record_id"].split("_")[-1]   # ARR_mitdb_105 -> 105
    cid = int(r["chunk_id"])
    exp = r["mem_sha256"]
    src = find_src(rid)
    if not src:
        print(f"  {r['case_id']}: SRC MISSING ({rid})", flush=True); miss.append(r['case_id']); continue
    start = SKIP + cid * WIN
    with open(src, "rb") as f:
        f.seek(start * 4)
        data = f.read(WIN * 4)
    if len(data) != WIN * 4:
        print(f"  {r['case_id']}: SHORT read {len(data)//4}/{WIN} (src {os.path.getsize(src)//4} samp)", flush=True)
        miss.append(r['case_id']); continue
    h = hashlib.sha256(data).hexdigest()
    ok = (h == exp)
    match += ok
    outp = os.path.join(OUT, r["case_id"] + ".mem")
    with open(outp, "wb") as o:
        o.write(data)
    manifest.append((r["case_id"], int(r["source_prediction_case_id"]), int(r["class_id"]), outp, ok))
    if not ok:
        miss.append(r['case_id'])
print(f"\nsha256 MATCH: {match}/{len(rows)}", flush=True)
if miss:
    print("MISMATCH/MISSING:", ", ".join(miss[:40]), flush=True)
# XSim manifest (case_id expected_class sample_count mempath) 저장
with open(OUT + "/xsim_manifest.txt", "w") as m:
    for cid, srccase, cls, path, ok in manifest:
        m.write(f"{srccase} {cls} {WIN} {path}\n")
print(f"manifest -> {OUT}/xsim_manifest.txt", flush=True)
