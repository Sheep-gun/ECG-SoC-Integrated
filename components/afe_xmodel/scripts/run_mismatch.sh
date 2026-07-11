#!/bin/bash
# [1.2] R/C mismatch 스윕: CMRR + 60Hz 잔차 + clipping (tb_afe_mm.sv, ecg_afe_xmodel_mm.sv)
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
W="$PRJ/sim_out/mismatch"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
ln -sf "$PRJ/data/real_ecg_100.pwl" real_ecg_100.pwl
"$VLIB" work >/dev/null
"$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
"$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv"    >c3.log 2>&1 || { echo C3; tail -20 c3.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel_mm.sv" >c4.log 2>&1 || { echo C4; tail -20 c4.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/tb/tb_afe_mm.sv"             >c5.log 2>&1 || { echo C5; tail -20 c5.log; exit 1; }
echo "COMPILE_OK"
run() { "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work -gMM=$1 tb_afe_mm XMODEL_global "+mode=$2" -do "run -all; quit -f" >/dev/null 2>&1; cp adc_mm.txt "$3"; }
for mm in 0 0.001 0.005 0.01; do
  echo "  running MM=$mm ..."
  run $mm cmrr  "adc_cmrr_$mm.txt"
  run $mm pli60 "adc_pli_$mm.txt"
done
echo "=== CMRR (공통모드 1V@10Hz 주입, 0.806mV/code, Adiff=201) ==="
for mm in 0 0.001 0.005 0.01; do
  awk -v M=$mm 'NR>1 && $1!~"#"{d=$2-2047;ss+=d*d;n++}
    END{rms=sqrt(ss/n); vout=rms*0.806e-3; acm=vout/0.7071;
        cmrr=(acm>0?20*log(201.0/acm)/log(10):999);
        printf "  MM=%-6s CMRR=%6.1f dB   (out_rms=%.2f codes)\n",M,cmrr,rms}' "adc_cmrr_$mm.txt"
done
echo "=== 60Hz PLI 잔차(MM=0 대비) + clipping (t>2s) ==="
for mm in 0 0.001 0.005 0.01; do
  paste <(grep -v '^#' adc_pli_0.txt|awk '{print $2}') <(grep -v '^#' "adc_pli_$mm.txt"|awk '{print $2}') | \
  awk -v M=$mm 'NR>2000{d=$1-$2;ss+=d*d;n++; c=$2; if(c<=0||c>=4095)clip++}
    END{printf "  MM=%-6s RMSdiff=%6.2f codes (%.2f mV)   clip=%d\n",M,sqrt(ss/n),sqrt(ss/n)*0.806,clip+0}'
done
echo "MISMATCH_DONE"
