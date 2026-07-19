open_vcd sample_feeder_smoke.vcd
log_vcd [get_objects -r /tb_axi_lite_axis_sample_feeder/*]
run all
close_vcd
quit
