#!/bin/bash
# [2.2] 50Hz vs 60Hz PLI 제거 비교 (tb_ecg_pli_freq.sv)
#   60Hz notch 중심 대비 50Hz에서 잔차가 얼마나 커지는지 정량화.
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
W="$PRJ/sim_out/pli_freq"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
ln -sf "$PRJ/data/real_ecg_100.pwl" real_ecg_100.pwl
"$VLIB" work >/dev/null
"$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
"$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/tb/tb_ecg_pli_freq.sv" >c4.log 2>&1 || { tail c4.log; exit 1; }
echo "COMPILE_OK"
run() { "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work tb_ecg_pli_freq XMODEL_global $1 -do "run -all; quit -f" >/dev/null 2>&1; cp adc_pli.txt "$2"; }
echo "[clean]";      run ""                              adc_clean.txt
echo "[60Hz inj]";   run "+fpli=60 +vcm=0.5 +vdiff=0.001" adc_60.txt
echo "[50Hz inj]";   run "+fpli=50 +vcm=0.5 +vdiff=0.001" adc_50.txt
echo "=== 잔차 비교 (깨끗한 ECG 대비, 0.806 mV/code, t>2s) ==="
for pair in "adc_60.txt:60Hz" "adc_50.txt:50Hz"; do
  f="${pair%%:*}"; lbl="${pair##*:}"
  paste <(grep -v '^#' adc_clean.txt|awk '{print $2}') <(grep -v '^#' "$f"|awk '{print $2}') | \
  awk -v L="$lbl" 'NR>2000{d=$1-$2;ss+=d*d;n++;a=(d<0?-d:d);if(a>mx)mx=a}
    END{printf "  %s PLI: RMS차 %.2f codes (%.3f mV), 최대 %.0f codes (%.2f mV)\n",L,sqrt(ss/n),sqrt(ss/n)*0.806,mx,mx*0.806}'
done
echo "PLI_FREQ_DONE"
