# ADC white-noise threshold — locked RTL final_pred (NSR chunk)

> 대상: NSR record 16483 w010 (clean golden = NSR 30/0/0/0). canonical 30분 chunk에 백색잡음 주입.
> claim: `noise ≤1 LSB rms에서 final_pred 안정`의 XSim result 근거. (worst-condition 16-case = `adc_nonideal_finalpred_xsim.csv`)

| noise_rms_lsb | clean_pred | pert_pred | flipped | final_mem (N/C/A/F) |
|---|---|---|---|---|
| 0.5 | NSR | NSR | false | 30/0/0/0 |
| 1.0 | NSR | NSR | false | 30/0/0/0 |
| 2.0 | NSR | CHF | true | 0/25/5/0 |

**noise 0.5·1.0 LSB → NSR 유지(30/0/0/0), 2.0 LSB에서만 CHF flip.** → classification stability는 noise ≤1 LSB에서 안정, 2 LSB는 extreme stress 민감성.
