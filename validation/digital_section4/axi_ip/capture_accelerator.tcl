open_vcd accelerator_smoke.vcd
log_vcd [get_objects -r /tb_snn_ecg_axi_smoke/*]
run all
close_vcd
quit
