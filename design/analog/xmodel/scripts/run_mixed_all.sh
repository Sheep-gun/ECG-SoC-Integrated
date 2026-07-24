#!/bin/bash
# 4클래스 Mixed-signal 통합: AFE(0~ENDSEC 실시간) → core, 창(STARTSEC~ENDSEC) 분류.
# 사용법: bash scripts/run_mixed_all.sh <endsec>   (기본 60)
set -uo pipefail
ENDSEC="${1:-60}"
XMODEL_HOME=$HOME/xmodel_2025.12_x86_64
QUESTA_HOME=$HOME/intelFPGA/25.1/questa_fse/questa_fse
export LD_LIBRARY_PATH="$XMODEL_HOME/lib/x86_64:${LD_LIBRARY_PATH:-}"
export SALMD_LICENSE_FILE=9524@52.79.127.207
export LM_LICENSE_FILE=$HOME/LR-164468_License.dat
export MGLS_LICENSE_FILE=$HOME/LR-164468_License.dat
export SALT_LICENSE_SERVER=$HOME/LR-164468_License.dat
PRJ="$(cd "$(dirname "$0")/.." && pwd)"
VLOG="$QUESTA_HOME/bin/vlog"; VLIB="$QUESTA_HOME/bin/vlib"; VSIM="$QUESTA_HOME/bin/vsim"
COMMON="-sv -mfcu +define+XMODEL +define+XMODEL_TIMEPRECISION=1ns +incdir+$XMODEL_HOME/include -work work"
W="$PRJ/sim_out/mixed"
python3 "$PRJ/scripts/convert_mem.py" >/dev/null
if [ ! -d "$W/work" ]; then
  mkdir -p "$W"; cd "$W" || exit 1; "$VLIB" work >/dev/null
  "$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
  "$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
  "$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
  "$VLOG" $COMMON "$PRJ"/digital/*.v >c4.log 2>&1 || { tail -20 c4.log; exit 1; }
  "$VLOG" $COMMON +acc "$PRJ/tb/tb_mixed_signal.sv" >c5.log 2>&1 || { tail -20 c5.log; exit 1; }
  echo "COMPILE_OK"
else cd "$W" || exit 1; fi
for c in NSR CHF ARR AFF; do
  ln -sf "$PRJ/data/ecg_$c.pwl" "ecg_$c.pwl"
  echo "[$c] 통합 시뮬 시작 ($(date +%H:%M:%S))"
  "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
     -work work tb_mixed_signal XMODEL_global "+pwl=ecg_$c.pwl" "+endsec=$ENDSEC" "+startsec=2" \
     -do "run -all; quit -f" 2>&1 | grep -E "MIXED_RESULT|Error|Fatal"
done
echo "ALL_DONE $(date +%H:%M:%S)"
