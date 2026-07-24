create_clock -name s_axi_aclk -period 10.000 [get_ports s_axi_aclk]

set_input_delay -clock [get_clocks s_axi_aclk] -max 2.000 [get_ports -quiet {
    s_axi_aresetn
    s_axi_awaddr[*] s_axi_awprot[*] s_axi_awvalid
    s_axi_wdata[*] s_axi_wstrb[*] s_axi_wvalid s_axi_bready
    s_axi_araddr[*] s_axi_arprot[*] s_axi_arvalid s_axi_rready
    s_axis_tdata[*] s_axis_tvalid s_axis_tlast
}]
set_input_delay -clock [get_clocks s_axi_aclk] -min 0.750 [get_ports -quiet {
    s_axi_aresetn
    s_axi_awaddr[*] s_axi_awprot[*] s_axi_awvalid
    s_axi_wdata[*] s_axi_wstrb[*] s_axi_wvalid s_axi_bready
    s_axi_araddr[*] s_axi_arprot[*] s_axi_arvalid s_axi_rready
    s_axis_tdata[*] s_axis_tvalid s_axis_tlast
}]

set_output_delay -clock [get_clocks s_axi_aclk] -max 2.000 [get_ports -quiet {
    s_axi_awready s_axi_wready s_axi_bresp[*] s_axi_bvalid
    s_axi_arready s_axi_rdata[*] s_axi_rresp[*] s_axi_rvalid
    s_axis_tready irq
}]
set_output_delay -clock [get_clocks s_axi_aclk] -min -0.750 [get_ports -quiet {
    s_axi_awready s_axi_wready s_axi_bresp[*] s_axi_bvalid
    s_axi_arready s_axi_rdata[*] s_axi_rresp[*] s_axi_rvalid
    s_axis_tready irq
}]

set_false_path -from [get_ports s_axi_aresetn]
