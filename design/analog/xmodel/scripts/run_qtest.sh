#!/bin/bash
# 노치 Q를 높여(좁게) ARR 플립이 복구되는지 검증 (디지털 등가 full 체인).
PRJ=$HOME/ECG-SoC
QH=$HOME/intelFPGA/25.1/questa_fse/questa_fse
export LM_LICENSE_FILE=$HOME/LR-164468_License.dat
export MGLS_LICENSE_FILE=$HOME/LR-164468_License.dat
for q in 10 15 20 40; do
  python3 "$PRJ/scripts/filter_mem.py" full "$q" "fullQ$q" >/dev/null
done
cd "$PRJ/sim_out/digref" || exit 1
echo "기준: raw ARR=2, AFE(Q5)통합 ARR=3 (NSR2 CHF1 AFF3 일정)"
for q in 10 15 20 40; do
  echo "--- 노치 Q=$q (full) ---"
  for c in NSR CHF ARR AFF; do
    ln -sf "$PRJ/data/mem_${c}_fullQ${q}.mem" "mem_${c}_fullQ${q}.mem"
    "$QH/bin/vsim" -c -work work tb_digital_ref "+mem=mem_${c}_fullQ${q}.mem" "+nsamp=60000" "+start=0" \
      -do "run -all; quit -f" 2>&1 | grep DIGREF
  done
done
