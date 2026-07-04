set repo_dir "C:/Users/YangGeon/SNN ECG Classifier"
set work_dir "C:/Users/YangGeon/_snn_ecg_microblaze_smoke_work"
set out_dir "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/microblaze_smoke"
set proj_dir "$work_dir/project"
set bd_name "snn_ecg_mb_smoke"
file mkdir $out_dir
file mkdir "$out_dir/reports"

create_project -force SNN_ECG_MB_SMOKE $proj_dir -part xc7a100tcsg324-1
set_property target_language Verilog [current_project]
set_property ip_repo_paths [list "$repo_dir/ip_repo"] [current_project]
update_ip_catalog

create_bd_design $bd_name

create_bd_port -dir I -type clk -freq_hz 100000000 CLK100MHZ
create_bd_port -dir I -type rst CPU_RESETN
set_property CONFIG.POLARITY ACTIVE_LOW [get_bd_ports CPU_RESETN]
create_bd_port -dir I UART_TXD_IN
create_bd_port -dir O UART_RXD_OUT

create_bd_cell -type ip -vlnv xilinx.com:ip:microblaze:* microblaze_0
set_property -dict [list \
    CONFIG.C_USE_INTERRUPT {1} \
    CONFIG.C_DEBUG_ENABLED {1} \
    CONFIG.C_USE_BARREL {1} \
    CONFIG.C_USE_DIV {1} \
    CONFIG.C_USE_HW_MUL {1} \
    CONFIG.C_USE_ICACHE {0} \
    CONFIG.C_USE_DCACHE {0} \
] [get_bd_cells microblaze_0]

apply_bd_automation -rule xilinx.com:bd_rule:microblaze -config [list \
    local_mem {64KB} \
    ecc {None} \
    cache {None} \
    debug_module {Debug Only} \
    axi_periph {Enabled} \
    axi_intc {0} \
    clk {/CLK100MHZ (100 MHz)} \
    rst {/CPU_RESETN} \
] [get_bd_cells microblaze_0]

create_bd_cell -type ip -vlnv user.org:user:snn_ecg_axi_accelerator:1.0 snn_ecg_axi_accelerator_0
set_property -dict [list \
    CONFIG.SNAPSHOT_SAMPLES {8} \
    CONFIG.SNAPSHOTS_PER_CHUNK {2} \
    CONFIG.POST_DONE_TICKS {37} \
    CONFIG.PROFILE_EN {1} \
    CONFIG.TLAST_CHECK_EN {1} \
] [get_bd_cells snn_ecg_axi_accelerator_0]

create_bd_cell -type ip -vlnv user.org:user:axi_lite_axis_sample_feeder:1.0 sample_feeder_0
set_property -dict [list \
    CONFIG.M_AXIS_TDATA_WIDTH {16} \
    CONFIG.FIFO_DEPTH {16} \
    CONFIG.FIFO_ADDR_WIDTH {4} \
] [get_bd_cells sample_feeder_0]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_uartlite:* axi_uartlite_0
set_property -dict [list CONFIG.C_BAUDRATE {115200} CONFIG.C_DATA_BITS {8} CONFIG.C_USE_PARITY {0}] [get_bd_cells axi_uartlite_0]

create_bd_cell -type ip -vlnv xilinx.com:ip:axi_intc:* axi_intc_0
set_property -dict [list CONFIG.C_KIND_OF_INTR {0x00000000} CONFIG.C_IRQ_CONNECTION {1}] [get_bd_cells axi_intc_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:* xlconcat_0
set_property CONFIG.NUM_PORTS {1} [get_bd_cells xlconcat_0]
create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:* axi_interconnect_0
set_property -dict [list CONFIG.NUM_MI {4} CONFIG.NUM_SI {1}] [get_bd_cells axi_interconnect_0]

connect_bd_intf_net [get_bd_intf_pins sample_feeder_0/m_axis] [get_bd_intf_pins snn_ecg_axi_accelerator_0/s_axis]
connect_bd_net [get_bd_ports UART_TXD_IN] [get_bd_pins axi_uartlite_0/rx]
connect_bd_net [get_bd_pins axi_uartlite_0/tx] [get_bd_ports UART_RXD_OUT]
connect_bd_net [get_bd_pins snn_ecg_axi_accelerator_0/irq] [get_bd_pins xlconcat_0/In0]
connect_bd_net [get_bd_pins xlconcat_0/dout] [get_bd_pins axi_intc_0/intr]
connect_bd_net [get_bd_pins axi_intc_0/irq] [get_bd_pins microblaze_0/Interrupt]

set rst_cells [get_bd_cells -quiet -hier -filter {VLNV =~ "xilinx.com:ip:proc_sys_reset:*"}]
if {[llength $rst_cells] == 0} {
    error "No proc_sys_reset cell found after MicroBlaze automation"
}
set rst_cell [lindex $rst_cells 0]
set resetn_pin [get_bd_pins $rst_cell/peripheral_aresetn]
if {[llength [get_bd_nets -quiet -of_objects [get_bd_pins $rst_cell/ext_reset_in]]] == 0} {
    connect_bd_net [get_bd_ports CPU_RESETN] [get_bd_pins $rst_cell/ext_reset_in]
}

connect_bd_intf_net [get_bd_intf_pins microblaze_0/M_AXI_DP] [get_bd_intf_pins axi_interconnect_0/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M00_AXI] [get_bd_intf_pins snn_ecg_axi_accelerator_0/s_axi]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M01_AXI] [get_bd_intf_pins sample_feeder_0/s_axi]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M02_AXI] [get_bd_intf_pins axi_uartlite_0/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_interconnect_0/M03_AXI] [get_bd_intf_pins axi_intc_0/s_axi]

foreach pin [list \
    [get_bd_pins axi_interconnect_0/ACLK] \
    [get_bd_pins axi_interconnect_0/S00_ACLK] \
    [get_bd_pins axi_interconnect_0/M00_ACLK] \
    [get_bd_pins axi_interconnect_0/M01_ACLK] \
    [get_bd_pins axi_interconnect_0/M02_ACLK] \
    [get_bd_pins axi_interconnect_0/M03_ACLK] \
    [get_bd_pins snn_ecg_axi_accelerator_0/s_axi_aclk] \
    [get_bd_pins sample_feeder_0/s_axi_aclk] \
    [get_bd_pins axi_uartlite_0/s_axi_aclk] \
    [get_bd_pins axi_intc_0/s_axi_aclk] \
] {
    if {[llength [get_bd_nets -quiet -of_objects $pin]] == 0} {
        connect_bd_net [get_bd_ports CLK100MHZ] $pin
    }
}

foreach pin [list \
    [get_bd_pins axi_interconnect_0/ARESETN] \
    [get_bd_pins axi_interconnect_0/S00_ARESETN] \
    [get_bd_pins axi_interconnect_0/M00_ARESETN] \
    [get_bd_pins axi_interconnect_0/M01_ARESETN] \
    [get_bd_pins axi_interconnect_0/M02_ARESETN] \
    [get_bd_pins axi_interconnect_0/M03_ARESETN] \
    [get_bd_pins snn_ecg_axi_accelerator_0/s_axi_aresetn] \
    [get_bd_pins sample_feeder_0/s_axi_aresetn] \
    [get_bd_pins axi_uartlite_0/s_axi_aresetn] \
    [get_bd_pins axi_intc_0/s_axi_aresetn] \
] {
    if {[llength [get_bd_nets -quiet -of_objects $pin]] == 0} {
        connect_bd_net $resetn_pin $pin
    }
}

set mb_data_space [get_bd_addr_spaces microblaze_0/Data]
assign_bd_address -target_address_space $mb_data_space -offset 0x44a00000 -range 4K [get_bd_addr_segs snn_ecg_axi_accelerator_0/s_axi/reg0]
assign_bd_address -target_address_space $mb_data_space -offset 0x44a10000 -range 4K [get_bd_addr_segs sample_feeder_0/s_axi/reg0]
assign_bd_address -target_address_space $mb_data_space -offset 0x40600000 -range 4K [get_bd_addr_segs axi_uartlite_0/S_AXI/Reg]
assign_bd_address -target_address_space $mb_data_space -offset 0x41200000 -range 4K [get_bd_addr_segs axi_intc_0/S_AXI/Reg]

validate_bd_design
save_bd_design
write_bd_tcl -force "$out_dir/snn_ecg_mb_smoke_bd.tcl"
set addr_fh [open "$out_dir/reports/system_bd_address.rpt" w]
puts $addr_fh "Long-window ECG 4-Class Accelerator MicroBlaze smoke address map"
puts $addr_fh "snn_ecg_axi_accelerator_0/s_axi/reg0 0x44a00000 4K"
puts $addr_fh "sample_feeder_0/s_axi/reg0          0x44a10000 4K"
puts $addr_fh "axi_uartlite_0/S_AXI/Reg            0x40600000 4K"
puts $addr_fh "axi_intc_0/S_AXI/Reg                0x41200000 4K"
close $addr_fh

make_wrapper -files [get_files "$proj_dir/SNN_ECG_MB_SMOKE.srcs/sources_1/bd/$bd_name/$bd_name.bd"] -top
add_files -norecurse "$proj_dir/SNN_ECG_MB_SMOKE.gen/sources_1/bd/$bd_name/hdl/${bd_name}_wrapper.v"
set_property top snn_ecg_mb_smoke_wrapper [current_fileset]
update_compile_order -fileset sources_1

add_files -fileset constrs_1 [list "$repo_dir/constraints/nexys_a7_microblaze_smoke.xdc"]

generate_target all [get_files "$proj_dir/SNN_ECG_MB_SMOKE.srcs/sources_1/bd/$bd_name/$bd_name.bd"]
export_ip_user_files -of_objects [get_files "$proj_dir/SNN_ECG_MB_SMOKE.srcs/sources_1/bd/$bd_name/$bd_name.bd"] -no_script -sync -force -quiet

set_property strategy Flow_PerfOptimized_high [get_runs synth_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore [get_runs impl_1]

launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property STATUS [get_runs synth_1]] != "synth_design Complete!"} {
    error "synth_1 failed: [get_property STATUS [get_runs synth_1]]"
}

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    error "impl_1 did not complete: [get_property STATUS [get_runs impl_1]]"
}
open_run impl_1
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file "$out_dir/reports/system_timing_summary.rpt"
report_cdc -details -file "$out_dir/reports/system_cdc.rpt"
report_clock_interaction -file "$out_dir/reports/system_clock_interaction.rpt"
report_methodology -file "$out_dir/reports/system_methodology.rpt"
report_drc -file "$out_dir/reports/system_drc.rpt"
report_io -file "$out_dir/reports/system_io.rpt"
report_route_status -file "$out_dir/reports/system_route_status.rpt"
report_utilization -file "$out_dir/reports/system_utilization.rpt"
report_utilization -hierarchical -file "$out_dir/reports/system_utilization_hier.rpt"
write_checkpoint -force "$out_dir/reports/system_routed.dcp"
report_ip_status -file "$out_dir/reports/system_ip_status.rpt"

set bit_file "$proj_dir/SNN_ECG_MB_SMOKE.runs/impl_1/snn_ecg_mb_smoke_wrapper.bit"
if {![file exists $bit_file]} {
    error "Bitstream not found: $bit_file"
}
file copy -force $bit_file "$out_dir/snn_ecg_mb_smoke.bit"

if {![catch {write_hw_platform -fixed -include_bit -force -file "$out_dir/snn_ecg_mb_smoke.xsa"} msg]} {
    puts "XSA=$out_dir/snn_ecg_mb_smoke.xsa"
} else {
    puts "WARN write_hw_platform failed: $msg"
}
exit
