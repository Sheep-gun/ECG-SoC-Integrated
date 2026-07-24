#!/bin/bash
# ================================================================
#  AFE 주파수 응답 + CMRR 특성 측정 (tb_afe_char.sv)
#  주파수 스윕으로 통과대역 이득·60Hz 노치 깊이·-3dB 대역폭·CMRR 산출.
#  사용법: bash scripts/run_char.sh          # 전체 스윕
#          bash scripts/run_char.sh "+freq=60"   # 단일 주파수
# ================================================================
set -uo pipefail
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
W="$PRJ/sim_out/char"
if [ ! -d "$W/work" ]; then
  rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
  "$VLIB" work >/dev/null
  "$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
  "$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
  "$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
  "$VLOG" $COMMON +acc "$PRJ/tb/tb_afe_char.sv" >c4.log 2>&1 || { tail c4.log; exit 1; }
  echo "COMPILE_OK"
else cd "$W" || exit 1; fi
run() { "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work tb_afe_char XMODEL_global $1 -do "run -all; quit -f" 2>&1 | grep "CHAR_RESULT"; }
if [ $# -ge 1 ]; then run "$1"; exit 0; fi
echo "=== DIFF 주파수 스윕 ==="
for f in 1 5 10 20 30 40 50 55 60 65 70 80 100 150 200; do run "+freq=$f"; done
echo "=== 공통모드(CMRR): 20Hz amp=0.1V ==="; run "+freq=20 +amp=0.1 +cm"
