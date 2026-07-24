#!/bin/bash
# Mixed-signal 통합 실행: AFE + 디지털 core 한 시뮬.
# 사용법: bash scripts/run_mixed.sh <CLASS> <endsec>   (예: NSR 10)
set -uo pipefail
CLS="${1:-NSR}"; ENDSEC="${2:-10}"
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
# PWL 준비
[ -f "$PRJ/data/ecg_$CLS.pwl" ] || python3 "$PRJ/scripts/convert_mem.py"
if [ ! -d "$W/work" ]; then
  mkdir -p "$W"; cd "$W" || exit 1
  "$VLIB" work >/dev/null
  echo "[1/5] xmodel_pkg"; "$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
  echo "[2/5] xmodel.f";  "$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
  echo "[3/5] AFE";       "$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
  echo "[4/5] 디지털 RTL"; "$VLOG" $COMMON "$PRJ"/digital/*.v >c4.log 2>&1 || { tail -20 c4.log; exit 1; }
  echo "[5/5] 통합 TB";    "$VLOG" $COMMON +acc "$PRJ/tb/tb_mixed_signal.sv" >c5.log 2>&1 || { tail -20 c5.log; exit 1; }
  echo "COMPILE_OK"
else cd "$W" || exit 1; fi
ln -sf "$PRJ/data/ecg_$CLS.pwl" "ecg_$CLS.pwl"
echo "=== [$CLS] 통합 시뮬 (endsec=$ENDSEC) ==="
"$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
   -work work tb_mixed_signal XMODEL_global "+pwl=ecg_$CLS.pwl" "+endsec=$ENDSEC" "+startsec=2" \
   -do "run -all; quit -f" 2>&1 | grep -iE "MIXED_RESULT|Error|Fatal|license" | head -20
