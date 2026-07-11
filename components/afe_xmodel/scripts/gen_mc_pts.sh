#!/bin/bash
W=$HOME/ECG-SoC/sim_out/multiclass
gen() {  # $1=file $2=yc
  grep -v '^#' "$1" | awk -v yc="$2" '$1>=2200 && $1<=5200 && ($1%3==0){
    x=60+($1-2200)/3000.0*680;
    y=yc-($2-2048)/500.0*42;
    if(y<yc-48)y=yc-48; if(y>yc+48)y=yc+48;
    printf "%.0f,%.0f ", x, y}'
  echo ""
}
gen "$W/adc_NSR.txt" 70
gen "$W/adc_ARR.txt" 190
gen "$W/adc_AFF.txt" 310
gen "$W/adc_CHF.txt" 430
