#!/bin/bash
# 4클래스(NSR/ARR/AFF/CHF) ECG를 AFE에 인가, 클래스별 ADC 로그 생성
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

python3 "$PRJ/scripts/convert_mem.py"
W="$PRJ/sim_out/multiclass"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
for c in NSR ARR AFF CHF; do ln -sf "$PRJ/data/ecg_$c.pwl" "ecg_$c.pwl"; done
"$VLIB" work >/dev/null
"$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
"$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/tb/tb_ecg_multiclass.sv" >c4.log 2>&1 || { tail c4.log; exit 1; }
echo "COMPILE_OK"
for c in NSR ARR AFF CHF; do
  echo "[$c] 시뮬..."
  "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work tb_ecg_multiclass XMODEL_global "+pwl=ecg_$c.pwl" "+out=adc_$c.txt" \
    -do "run -all; quit -f" >/dev/null 2>&1
  echo "  $(grep -vc '^#' adc_$c.txt) 샘플"
done
echo "DONE"
