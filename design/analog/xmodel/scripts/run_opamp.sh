#!/bin/bash
# [2.4] op-amp finite GBW / VOS 스윕 (tb_afe_op.sv, ecg_afe_xmodel_op.sv)
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
W="$PRJ/sim_out/opamp"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
ln -sf "$PRJ/data/real_ecg_100.pwl" real_ecg_100.pwl
"$VLIB" work >/dev/null
"$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
"$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel_op.sv" >c3.log 2>&1 || { echo C3; tail -20 c3.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/tb/tb_afe_op.sv"             >c4.log 2>&1 || { echo C4; tail -20 c4.log; exit 1; }
echo "COMPILE_OK"
run() { "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work -gGBW_HZ=$1 -gVOS=$2 tb_afe_op XMODEL_global -do "run -all; quit -f" >/dev/null 2>&1; cp adc_op.txt "$3"; }
echo "  ref(ideal) ..."; run 1e9 0.0 adc_ideal.txt
for g in 100000 500000 1000000 5000000; do echo "  GBW=$g ..."; run $g 0.0 "adc_gbw_$g.txt"; done
for v in 0.0005 0.001 0.002;               do echo "  VOS=$v ..."; run 1e9 $v "adc_vos_$v.txt"; done
anal() { # $1=file $2=label ; ideal 대비 RMS차 + 평균offset(코드) + clipping (t>2s)
  paste <(grep -v '^#' adc_ideal.txt|awk '{print $2}') <(grep -v '^#' "$1"|awk '{print $2}') | \
  awk -v L="$2" 'NR>2000{d=$1-$2;ss+=d*d;n++; s2+=($2-2047); if($2<=0||$2>=4095)clip++}
    END{printf "  %-14s RMSdiff=%6.2f codes  meanOffset=%+7.2f codes(%.2f mV)  clip=%d\n",
        L,sqrt(ss/n),s2/n,(s2/n)*0.806,clip+0}'
}
echo "=== finite GBW (VOS=0, ideal 대비) ==="
for g in 100000 500000 1000000 5000000; do anal "adc_gbw_$g.txt" "GBW=${g}Hz"; done
echo "=== input VOS (GBW=ideal) ==="
for v in 0.0005 0.001 0.002; do anal "adc_vos_$v.txt" "VOS=${v}V"; done
echo "OPAMP_DONE"
