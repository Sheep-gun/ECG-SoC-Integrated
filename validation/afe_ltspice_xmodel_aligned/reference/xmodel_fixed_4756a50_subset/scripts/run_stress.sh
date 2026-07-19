#!/bin/bash
# [1.3] 전극 DC offset / baseline wander 스트레스 (tb_ecg_stress.sv)
#   HPF(IA 이전)가 offset/wander 제거 → 정착 후 ADC clipping 0 / clean 대비 잔차 확인.
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
W="$PRJ/sim_out/stress"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
ln -sf "$PRJ/data/real_ecg_100.pwl" real_ecg_100.pwl
"$VLIB" work >/dev/null
"$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
"$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
"$VLOG" $COMMON +acc "$PRJ/tb/tb_ecg_stress.sv" >c4.log 2>&1 || { tail c4.log; exit 1; }
echo "COMPILE_OK"
run() { "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
    -work work tb_ecg_stress XMODEL_global $1 -do "run -all; quit -f" >/dev/null 2>&1; cp adc_stress.txt "$2"; }
run ""                          adc_clean.txt
run "+dcoff=0.010"              adc_dc010.txt
run "+dcoff=0.050"              adc_dc050.txt
run "+dcoff=0.100"              adc_dc100.txt
run "+dcoff=0.200"              adc_dc200.txt
run "+dcoff=-0.200"             adc_dcm200.txt
run "+bwamp=0.001 +bwfreq=0.1"  adc_bw1.txt
run "+bwamp=0.002 +bwfreq=0.2"  adc_bw2.txt
echo "=== 분석: clipping / 정착후(t>2s) clean대비 잔차 (0.806 mV/code) ==="
printf "%-22s %8s %10s %12s %10s\n" case clipTot clip_t>2s RMSdiff_code recover_s
for pair in "adc_clean.txt:clean" "adc_dc010.txt:dc+10mV" "adc_dc050.txt:dc+50mV" \
            "adc_dc100.txt:dc+100mV" "adc_dc200.txt:dc+200mV" "adc_dcm200.txt:dc-200mV" \
            "adc_bw1.txt:bw0.1Hz1mV" "adc_bw2.txt:bw0.2Hz2mV"; do
  f="${pair%%:*}"; lbl="${pair##*:}"
  paste <(grep -v '^#' adc_clean.txt|awk '{print $2}') <(grep -v '^#' "$f"|awk '{print $2}') | \
  awk -v L="$lbl" '{c=$2;
      if(c<=0||c>=4095){ct++; if(NR>2000)ct2++}
      if(NR>2000){d=$1-$2;ss+=d*d;n++}
      # 정착 회복: |c-clean|이 마지막으로 20코드 초과한 시점(초)
      if(NR<=2000){dd=$1-$2; if(dd<0)dd=-dd; if(dd>20)rec=NR}
    }
    END{printf "%-22s %8d %10d %12.2f %10.3f\n",L,ct,ct2,(n?sqrt(ss/n):0),rec/1000.0}'
done
echo "STRESS_DONE"
