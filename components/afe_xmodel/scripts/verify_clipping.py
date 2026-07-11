#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [검증 1.1] 전체 final dataset clipping / headroom 검증
#   대상 (a) full-record 전체 DB 127 record (fullrec_afe + fullrec_afe_remaining, signed .mem)
#        (b) strict60_large "final_test" 60s 세그먼트 (afe_output_xmodelmatch, signed .mem)
#   측정: ADC unsigned code min/max, count(==0), count(==4095), clip ratio
#         head 2s(HPF settling) 제외 전/후 분리
#   출력: docs/afe_stress/clipping_report_*.csv + stdout 요약
import os as _os, pathlib as _pl
_ROOT = _os.environ.get('ECG_SOC_ROOT', str(_pl.Path(__file__).resolve().parents[1]))
import os, sys, csv, glob
import numpy as np

ECG = _ROOT + ""
OUTDIR = ECG + "/docs/afe_stress"
os.makedirs(OUTDIR, exist_ok=True)
SETTLE = 2000  # 앞 2s(2000샘플) = HPF 과도구간

def _hexval(col):
    # ascii byte -> hex digit value ('0'-'9','a'-'f','A'-'F')
    return np.where(col >= 97, col - 87, np.where(col >= 65, col - 55, col - 48)).astype(np.int32)

def read_unsigned(path):
    # .mem = signed 2's-comp 12-bit hex (3-hex).  unsigned_code = h ^ 0x800 (MSB flip)
    buf = np.fromfile(path, dtype=np.uint8)
    # fast path: 고정폭 'xxx\n' (4바이트/샘플, WSL 생성물 = LF) → 완전 벡터화
    if buf.size % 4 == 0 and buf.size > 0:
        m = buf.reshape(-1, 4)
        if np.all(m[:, 3] == 10):
            h = _hexval(m[:, 0]) * 256 + _hexval(m[:, 1]) * 16 + _hexval(m[:, 2])
            return (h & 0xFFF) ^ 0x800
    # fallback: 토큰 파싱 (CRLF/불규칙 폭 대비, 소형 파일용)
    txt = buf.tobytes().decode("ascii", "ignore").split()
    h = np.array([int(t, 16) for t in txt], dtype=np.int32)
    return (h & 0xFFF) ^ 0x800

def scan_record(path):
    u = read_unsigned(path)
    n = len(u)
    body = u[SETTLE:] if n > SETTLE else u[:0]
    def stats(a):
        if len(a) == 0:
            return dict(n=0, mn=None, mx=None, c0=0, c4095=0, ratio=0.0)
        return dict(n=len(a), mn=int(a.min()), mx=int(a.max()),
                    c0=int((a == 0).sum()), c4095=int((a == 4095).sum()),
                    ratio=float(((a == 0) | (a == 4095)).sum()) / len(a))
    return n, stats(u), stats(body)

def run_set(name, files, keyfn):
    rows = []
    print(f"\n=== [{name}] {len(files)} records ===", flush=True)
    for p in sorted(files):
        cls, rid = keyfn(p)
        n, full, body = scan_record(p)
        rows.append(dict(dataset=name, class_label=cls, record_id=rid, n_samples=n,
                         full_min=full['mn'], full_max=full['mx'],
                         full_clip=full['c0'] + full['c4095'], full_clip_ratio=round(full['ratio'], 8),
                         body_min=body['mn'], body_max=body['mx'],
                         body_clip=body['c0'] + body['c4095'], body_clip_ratio=round(body['ratio'], 8)))
    # 요약
    tot_full = sum(r['full_clip'] for r in rows)
    tot_body = sum(r['body_clip'] for r in rows)
    tot_n = sum(r['n_samples'] for r in rows)
    gmin = min(r['body_min'] for r in rows if r['body_min'] is not None)
    gmax = max(r['body_max'] for r in rows if r['body_max'] is not None)
    print(f"  records={len(rows)}  total_samples={tot_n:,}")
    print(f"  clip(head 2s 포함) = {tot_full}   clip(head 2s 제외) = {tot_body}")
    print(f"  body code 범위(전 record min~max) = {gmin} ~ {gmax}  (full-scale 0~4095, headroom {gmin}LSB / {4095-gmax}LSB)")
    worst = max(rows, key=lambda r: r['body_clip_ratio'])
    print(f"  worst body clip ratio = {worst['body_clip_ratio']:.6%}  @ {worst['class_label']}/{worst['record_id']}")
    return rows

def key_fullrec(p):
    parts = p.replace("\\", "/").split("/")
    return parts[-2], os.path.splitext(parts[-1])[0]

def key_xmm(p):
    # .../<split>/signed/<file>.mem  → class는 파일명/매니페스트에서 유추 어려움 → split 표기
    return "seg", os.path.splitext(os.path.basename(p))[0]

def main():
    all_rows = []
    # (a) full-record 전체 DB
    fr = glob.glob(ECG + "/datasets/fullrec_afe/*/*/*.mem") + \
         glob.glob(ECG + "/datasets/fullrec_afe_remaining/*/*/*.mem")
    # x_*.mem (보조 리드 변형) 제외 옵션 없이 전부 포함
    all_rows += run_set("fullrec_DB_127", fr, key_fullrec)

    # (b) strict60_large "final_test" 세그 (xmodelmatch signed = 분류기 실입력 60s chunk)
    for sp in ["test", "val", "train"]:
        xs = glob.glob(ECG + f"/datasets/afe_output_xmodelmatch/{sp}/signed/*.mem")
        if xs:
            all_rows += run_set(f"xmodelmatch_{sp}", xs, key_xmm)

    outp = os.path.join(OUTDIR, "clipping_report.csv")
    with open(outp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()))
        w.writeheader(); w.writerows(all_rows)
    print(f"\nCSV -> {outp}  ({len(all_rows)} rows)")

if __name__ == "__main__":
    main()
