#!/usr/bin/env bash
set -euo pipefail

# Required licensed tools. No license address is embedded in validation output.
: "${XMODEL_HOME:?Set XMODEL_HOME to the licensed XMODEL installation}"
: "${QUESTA_HOME:?Set QUESTA_HOME to the Questa installation}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "$ROOT/../../.." && pwd)"
FIXED="$REPO_ROOT/design/analog/xmodel"
TB="$ROOT/reference/xmodel_alignment/tb_xmodel_correlation.sv"
WORK="$ROOT/results/xmodel_aligned/xmodel_reference/work"
OUT="$ROOT/results/xmodel_aligned/xmodel_reference"
VLIB="$QUESTA_HOME/bin/vlib"
VLOG="$QUESTA_HOME/bin/vlog"
VSIM="$QUESTA_HOME/bin/vsim"
COMMON=(-sv -mfcu +define+XMODEL +define+XMODEL_TIMEPRECISION=1ns "+incdir+$XMODEL_HOME/include" -work work)

rm -rf "$WORK"
mkdir -p "$WORK" "$OUT"
cp "$ROOT/../patient100_ecg_10s.txt" "$WORK/patient100_ecg_10s.txt"
cd "$WORK"
"$VLIB" work
"$VLOG" "${COMMON[@]}" "$XMODEL_HOME/include/xmodel_pkg.sv" > compile_pkg.log 2>&1
"$VLOG" "${COMMON[@]}" -f "$XMODEL_HOME/include/xmodel.f" > compile_primitives.log 2>&1
"$VLOG" "${COMMON[@]}" "$FIXED/analog/ecg_afe_xmodel.sv" > compile_dut.log 2>&1
"$VLOG" "${COMMON[@]}" "$TB" > compile_tb.log 2>&1
"$VSIM" -c -t 1ns -sv_lib "$XMODEL_HOME/lib/x86_64/xmodel_msim" \
  -pli "$XMODEL_HOME/lib/x86_64/xmodel_msim.sl" -work work \
  tb_xmodel_correlation XMODEL_global -do "run -all; quit -f" > simulate.log 2>&1
cp adc_nominal.txt "$OUT/adc_nominal.txt"
echo "XMODEL reference: $OUT/adc_nominal.txt"
echo "Next: python scripts/compare_xmodel_ltspice.py"
