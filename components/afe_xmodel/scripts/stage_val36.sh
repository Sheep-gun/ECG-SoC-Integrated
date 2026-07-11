#!/bin/bash
# [1.4] emu↔XModel 36세그 검증용 스테이징: test split에서 클래스당 9세그(=36) 선택
set -e
D=$HOME/ECG-SoC/datasets/strict60_large/raw/test/mem
W=$HOME/ECG-SoC/sim_out/afe_val
mkdir -p "$W/raw" "$W/emu" "$W/xmodel" "$W/pwl"
rm -f "$W/raw"/*.mem "$W/emu"/*.adc "$W/xmodel"/*.adc "$W/pwl"/*.pwl "$W"/conc_*.adc "$W"/conc_*.log
: > "$W/list.txt"
for c in NSR CHF ARR AFF; do
  ls "$D"/*.mem | sort | awk -F/ -v c="_${c}_" '$NF ~ c' | head -9 | while read -r f; do
    cp "$f" "$W/raw/"
    basename "$f" >> "$W/list.txt"
  done
done
echo "staged $(wc -l < "$W/list.txt") segments into $W/raw"
sort "$W/list.txt" | awk -F_ '{print $2}' | uniq -c
