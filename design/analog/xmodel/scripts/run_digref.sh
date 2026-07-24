#!/bin/bash
# 디지털 단독 기준치: 4클래스 원본 .mem을 core에 직접 주입 (AFE 없음, 빠름)
set -uo pipefail
QUESTA_HOME=$HOME/intelFPGA/25.1/questa_fse/questa_fse
export LM_LICENSE_FILE=$HOME/LR-164468_License.dat
export MGLS_LICENSE_FILE=$HOME/LR-164468_License.dat
PRJ="$(cd "$(dirname "$0")/.." && pwd)"
VLOG="$QUESTA_HOME/bin/vlog"; VLIB="$QUESTA_HOME/bin/vlib"; VSIM="$QUESTA_HOME/bin/vsim"
W="$PRJ/sim_out/digref"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
"$VLIB" work >/dev/null
"$VLOG" -sv -mfcu -work work "$PRJ"/digital/*.v >c1.log 2>&1 || { tail -20 c1.log; exit 1; }
"$VLOG" -sv -mfcu -work work "$PRJ/tb/tb_digital_ref.sv" >c2.log 2>&1 || { tail c2.log; exit 1; }
echo "COMPILE_OK (기대: NSR=0 CHF=1 ARR=2 AFF=3)"
NS="${1:-60000}"; ST="${2:-0}"
for c in NSR CHF ARR AFF; do
  ln -sf "$PRJ/data/mem_$c.mem" "mem_$c.mem"
  "$VSIM" -c -work work tb_digital_ref "+mem=mem_$c.mem" "+nsamp=$NS" "+start=$ST" -do "run -all; quit -f" 2>&1 | grep "DIGREF"
done
