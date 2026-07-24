#!/bin/bash
# ================================================================
#  ECG AFE Mixed-Signal 시뮬레이션 (XModel + Questa)
#  실제 MIT-BIH ECG(data/real_ecg_100.pwl)를 인가, 12-bit ADC 출력 로그 생성.
#
#  사용법:
#    bash scripts/run_afe_sim.sh            # 전체 5초 (VCD off, ~25s, 5000샘플)
#    bash scripts/run_afe_sim.sh vcd 300ms  # 300ms만 + 전계층 VCD (파형 관찰용)
#
#  전제: Questa 라이선스 hostid는 qsim-license-nic.service가 loopback0에 설정
#        (부팅 자동). 미설정 시 'sudo systemctl restart qsim-license-nic' 후 재시도.
# ================================================================
set -uo pipefail
MODE="${1:-full}"; DUR="${2:-all}"
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

# 라이선스 hostid 확인
LB=$(cat /sys/class/net/loopback0/address 2>/dev/null || echo "")
[ "$LB" = "00:15:5d:84:ee:1a" ] || echo "[!] loopback0 MAC=$LB (기대 00:15:5d:84:ee:1a). 'sudo systemctl restart qsim-license-nic' 필요할 수 있음."

mkdir -p "$PRJ/data"
[ -f "$PRJ/data/real_ecg_100.pwl" ] || cp $HOME/real_ecg_100.pwl "$PRJ/data/" 2>/dev/null || true
W="$PRJ/sim_out/run"; rm -rf "$W"; mkdir -p "$W"; cd "$W" || exit 1
ln -sf "$PRJ/data/real_ecg_100.pwl" real_ecg_100.pwl

# VCD off 모드: tb의 $dumpfile/$dumpvars 제거본 사용(대용량 VCD 방지)
if [ "$MODE" = "vcd" ]; then TB="$PRJ/tb/tb_ecg_afe.sv"; else
  sed -E '/\$dumpfile|\$dumpvars/d' "$PRJ/tb/tb_ecg_afe.sv" > tb_run.sv; TB="tb_run.sv"; DUR="${2:-all}"
fi

"$VLIB" work >/dev/null
echo "[1/4] xmodel_pkg"; "$VLOG" $COMMON "$XMODEL_HOME/include/xmodel_pkg.sv" >c1.log 2>&1 || { tail c1.log; exit 1; }
echo "[2/4] xmodel.f";  "$VLOG" $COMMON -f "$XMODEL_HOME/include/xmodel.f"  >c2.log 2>&1 || { tail c2.log; exit 1; }
echo "[3/4] design";    "$VLOG" $COMMON +acc "$PRJ/analog/ecg_afe_xmodel.sv" >c3.log 2>&1 || { tail -20 c3.log; exit 1; }
echo "[4/4] tb";        "$VLOG" $COMMON +acc "$TB" >c4.log 2>&1 || { tail c4.log; exit 1; }
echo "  컴파일 OK"

[ "$DUR" = "all" ] && DOCMD="run -all; quit -f" || DOCMD="run $DUR; quit -f"
"$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
   -work work tb_ecg_afe XMODEL_global -do "$DOCMD" 2>&1 | grep -iE "license|Error|Info|complete" | head -20
echo "=== 결과: $W/adc_output.txt (유효샘플 $(grep -vc '^#' adc_output.txt 2>/dev/null)) ==="
[ "$MODE" = "vcd" ] && echo "    VCD: $W/ecg_result.vcd"
