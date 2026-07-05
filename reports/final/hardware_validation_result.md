# Hardware Validation Result

## Summary

The locked RTL has been checked through Python/XSim comparison, Vivado implementation, IP-XACT packaging, and Vitis/MicroBlaze class-wise full-record replay.

| Layer | Result |
|---|---|
| Python vs XSim locked final layer | final_pred/final_mem mismatch 0 over 36 final_test cases |
| Pure RTL Vivado | LUT/FF/BRAM/DSP 9719/5038/0/0, WNS 8.184 ns |
| OOC/profile Vivado | LUT/FF/BRAM/DSP 9905/5769/0/0, WNS 0.471 ns |
| IP packaging | AXI accelerator and sample feeder IP-XACT packages present |
| MicroBlaze full replay build | bitstream/XSA/ELF generated, timing met |
| Board replay | NSR/CHF/ARR/AFF one 30-minute case each, final_pred/final_mem exact 4/4 |

## Boundary

This is engineering validation of an FPGA/VLSI prototype. It is not medical diagnosis validation, physical AFE board measurement, ADC silicon measurement, or transistor-level layout verification.
