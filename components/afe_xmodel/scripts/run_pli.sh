#!/bin/bash
# ================================================================
#  60Hz 전원선 간섭(PLI) 제거 검증 (tb_ecg_pli.sv)
#  실제 ECG에 60Hz 공통모드/차동 간섭을 주입, 깨끗한 ECG 대비 잔차 측정.
#  사용법: bash scripts/run_pli.sh
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
W="$PRJ/sim_out/pli"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
ln -sf "$PRJ/data/real_ecg_100.pwl" real_ecg_100.pwl
"$VLIB" work >/dev/null
"$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
"$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/tb/tb_ecg_pli.sv" >c4.log 2>&1 || { tail c4.log; exit 1; }
echo "COMPILE_OK"
runpli() { "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work tb_ecg_pli XMODEL_global $1 -do "run -all; quit -f" >/dev/null 2>&1; cp adc_pli.txt "$2"; }
echo "[A] 깨끗한 ECG";              runpli "" adc_clean.txt
echo "[B] +60Hz CM0.5V+차동1mV";    runpli "+vcm=0.5 +vdiff=0.001" adc_pli_strong.txt
echo "[C] +60Hz CM1V+차동2mV(극한)"; runpli "+vcm=1.0 +vdiff=0.002" adc_pli_extreme.txt
echo "=== 잔차 비교 (0.806 mV/code) ==="
for pair in "adc_pli_strong.txt:강" "adc_pli_extreme.txt:극한"; do
  f="${pair%%:*}"; lbl="${pair##*:}"
  paste <(grep -v '^#' adc_clean.txt|awk '{print $2}') <(grep -v '^#' "$f"|awk '{print $2}') | \
  awk -v L="$lbl" 'NR>2000{d=$1-$2;ss+=d*d;n++;a=(d<0?-d:d);if(a>mx)mx=a}
    END{printf "  %s: RMS차 %.2f codes (%.3f mV), 최대 %.0f codes (%.2f mV)\n",L,sqrt(ss/n),sqrt(ss/n)*0.806,mx,mx*0.806}'
done
