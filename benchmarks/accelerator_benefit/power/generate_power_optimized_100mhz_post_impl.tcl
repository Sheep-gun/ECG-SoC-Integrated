set script_dir [file dirname [file normalize [info script]]]
set work_dir [file normalize [file join $script_dir "work" "pure_rtl_100mhz"]]
set result_dir [file normalize [file join $script_dir "results" "pure_rtl_100mhz_power_opt"]]
set synth_dcp [file normalize [file join $work_dir "project" "SNN_ECG_PURE_RTL_100MHZ_POWER.runs" "synth_1" "snn_ecg_v2_nexys_a7_100mhz_top.dcp"]]
set output_dcp [file normalize [file join $work_dir "pure_rtl_100mhz_power_opt_routed.dcp"]]
set constraint_file [file normalize [file join $script_dir "constraints" "nexys_a7_snn_ecg_v2_100mhz.xdc"]]

if {![file exists $synth_dcp]} {
    error "Missing baseline synthesis checkpoint: $synth_dcp"
}
file mkdir $result_dir
open_checkpoint $synth_dcp
# Vivado 2020.2 read_xdc mis-resolves this workspace path because it contains
# spaces; sourcing the XDC applies the same Tcl constraints deterministically.
source $constraint_file
opt_design
power_opt_design
report_power_opt -file [file join $result_dir "pure_rtl_100mhz_power_opt_transformations.rpt"]
place_design
phys_opt_design
route_design

report_utilization -file [file join $result_dir "pure_rtl_100mhz_power_opt_utilization_post_route.rpt"]
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file [file join $result_dir "pure_rtl_100mhz_power_opt_timing_post_route.rpt"]
report_power -file [file join $result_dir "pure_rtl_100mhz_power_opt_vectorless_power_post_route.rpt"]
write_checkpoint -force $output_dcp

set wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
set timing_status "FAILED"
if {$wns >= 0.0} {
    set timing_status "MET"
}
set env_file [open [file join $result_dir "pure_rtl_100mhz_power_opt_environment.txt"] "w"]
puts $env_file "VIVADO_VERSION=[version -short]"
puts $env_file "PART=[get_property PART [current_design]]"
puts $env_file "TOP=[get_property TOP [current_design]]"
puts $env_file "IMPLEMENTATION_STATUS=routed"
puts $env_file "TIMING_STATUS=$timing_status"
puts $env_file "WNS_NS=$wns"
puts $env_file "CONSTRAINT=$constraint_file"
puts $env_file "OPTIMIZATION=opt_design; power_opt_design; place_design; phys_opt_design; route_design"
puts $env_file "POWER_OPT_SCOPE=Vivado intelligent clock gating based on existing clock enables; no functional RTL change"
foreach clk [get_clocks] {
    puts $env_file "CLOCK=$clk PERIOD_NS=[get_property PERIOD $clk]"
}
close $env_file
close_design
exit
