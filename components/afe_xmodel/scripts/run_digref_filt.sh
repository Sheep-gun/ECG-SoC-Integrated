#!/bin/bash
# 디지털 필터(AFE 등가)만 적용한 .mem을 digref로 분류 → 원인 격리.
set -uo pipefail
QUESTA_HOME=$HOME/intelFPGA/25.1/questa_fse/questa_fse
export LM_LICENSE_FILE=$HOME/LR-164468_License.dat
export MGLS_LICENSE_FILE=$HOME/LR-164468_License.dat
PRJ="$(cd "$(dirname "$0")/.." && pwd)"
VSIM="$QUESTA_HOME/bin/vsim"
W="$PRJ/sim_out/digref"   # 기존 컴파일 work 재사용
MODES="${*:-lpf full}"
for m in $MODES; do python3 "$PRJ/scripts/filter_mem.py" "$m" >/dev/null; done
cd "$W" || exit 1
echo "기준: raw digref = NSR2 CHF1 ARR2 AFF3 / AFE통합 = NSR2 CHF1 ARR3 AFF3"
for mode in $MODES; do
  echo "--- mode=$mode (전체 60s) ---"
  for c in NSR CHF ARR AFF; do
    ln -sf "$PRJ/data/mem_${c}_${mode}.mem" "mem_${c}_${mode}.mem"
    "$VSIM" -c -work work tb_digital_ref "+mem=mem_${c}_${mode}.mem" "+nsamp=60000" "+start=0" \
      -do "run -all; quit -f" 2>&1 | grep "DIGREF"
  done
done
