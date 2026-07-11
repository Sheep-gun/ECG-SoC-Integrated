#!/bin/bash
# XModel 라이선스 동시실행(병렬) 가능 여부 경험적 테스트: N개 vsim 동시 기동, 체크아웃 성공/거부 집계.
set -uo pipefail
XMODEL_HOME=$HOME/xmodel_2025.12_x86_64
QUESTA_HOME=$HOME/intelFPGA/25.1/questa_fse/questa_fse
export LD_LIBRARY_PATH="$XMODEL_HOME/lib/x86_64:${LD_LIBRARY_PATH:-}"
export SALMD_LICENSE_FILE=9524@52.79.127.207
export LM_LICENSE_FILE=$HOME/LR-164468_License.dat
export MGLS_LICENSE_FILE=$HOME/LR-164468_License.dat
export SALT_LICENSE_SERVER=$HOME/LR-164468_License.dat
VSIM="$QUESTA_HOME/bin/vsim"
W=$HOME/ECG-SoC/sim_out/afe_val
cd "$W" || exit 1
mapfile -t PW < <(ls pwl/*.pwl | head -4)
N=${1:-3}
echo "launching $N concurrent XModel sims ($(date +%H:%M:%S)) ..."
pids=()
for i in $(seq 0 $((N-1))); do
  p="${PW[$((i % ${#PW[@]}))]}"
  "$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" \
     -work work tb_afe_batch XMODEL_global "+pwl=$p" "+endsec=3" "+out=conc_$i.adc" \
     -do "run -all; quit -f" > "conc_$i.log" 2>&1 &
  pids+=($!)
  echo "  started #$i pid=${pids[$((i))]}"
done
for pid in "${pids[@]}"; do wait "$pid"; done
echo "=== per-run results ($(date +%H:%M:%S)) ==="
ok=0
for i in $(seq 0 $((N-1))); do
  co=$(grep -c "successfully checked out" "conc_$i.log")
  den=$(grep -ciE "number of users|denied|not available|reached|cannot find license|FLEXlm error|Maximum" "conc_$i.log")
  fin=$(grep -c "AFE_BATCH_DONE" "conc_$i.log")
  echo "#$i: checkout=$co  denied=$den  finished=$fin"
  [ "$fin" -ge 1 ] && ok=$((ok+1))
done
echo "=== SUCCESSFUL CONCURRENT RUNS: $ok / $N ==="
echo "--- any license-limit messages (raw) ---"
grep -hiE "number of users|denied|not available|reached|Maximum|FLEXlm error" conc_*.log | sort -u | head
echo CONC_TEST_DONE
