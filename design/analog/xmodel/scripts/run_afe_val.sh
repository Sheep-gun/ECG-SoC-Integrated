#!/bin/bash
# 검증용: 스테이징된 세그먼트들을 XModel AFE로 실행 → unsigned ADC .adc 출력 (시간측정)
set -uo pipefail
XMODEL_HOME=$HOME/xmodel_2025.12_x86_64
QUESTA_HOME=$HOME/intelFPGA/25.1/questa_fse/questa_fse
export LD_LIBRARY_PATH="$XMODEL_HOME/lib/x86_64:${LD_LIBRARY_PATH:-}"
export SALMD_LICENSE_FILE=9524@52.79.127.207
export LM_LICENSE_FILE=$HOME/LR-164468_License.dat
export MGLS_LICENSE_FILE=$HOME/LR-164468_License.dat
export SALT_LICENSE_SERVER=$HOME/LR-164468_License.dat
PRJ=$HOME/ECG-SoC
VLOG="$QUESTA_HOME/bin/vlog"; VLIB="$QUESTA_HOME/bin/vlib"; VSIM="$QUESTA_HOME/bin/vsim"
COMMON="-sv -mfcu +define+XMODEL +define+XMODEL_TIMEPRECISION=1ns +incdir+$XMODEL_HOME/include -work work"
W="$PRJ/sim_out/afe_val"
VAL="$W/raw"
mkdir -p "$W/xmodel" "$W/pwl"
cd "$W" || exit 1
if [ ! -d "$W/work" ]; then
  "$VLIB" work >/dev/null
  "$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { echo COMPILE_FAIL1; tail c1.log; exit 1; }
  "$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"   >c2.log 2>&1 || { echo COMPILE_FAIL2; tail c2.log; exit 1; }
  "$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { echo COMPILE_FAIL3; tail -20 c3.log; exit 1; }
  "$VLOG" $COMMON +acc "$PRJ/tb/tb_afe_batch.sv"       >c5.log 2>&1 || { echo COMPILE_FAIL5; tail -20 c5.log; exit 1; }
  echo "COMPILE_OK $(date +%H:%M:%S)"
fi
for f in $(cat "$W/list.txt"); do
  base="${f%.mem}"
  python3 "$PRJ/scripts/mem2pwl.py" "$VAL/$f" "$W/pwl/$base.pwl" 60
  t0=$(date +%s)
  "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
     -work work tb_afe_batch XMODEL_global "+pwl=$W/pwl/$base.pwl" "+endsec=60" "+out=$W/xmodel/$base.adc" \
     -do "run -all; quit -f" >"$W/vsim_$base.log" 2>&1
  t1=$(date +%s)
  echo "[$base] ${base##*_}  wall=$((t1-t0))s  lines=$(wc -l < "$W/xmodel/$base.adc" 2>/dev/null)  $(grep -c -iE 'error|fatal' "$W/vsim_$base.log") err"
done
echo "AFE_VAL_DONE $(date +%H:%M:%S)"
