set script_dir [file dirname [file normalize [info script]]]
set repo_dir [file normalize [file join $script_dir ".." ".." ".."]]
set work_dir [file normalize [file join $::env(USERPROFILE) "_snn_ecg_power_mb"]]
set checkpoint_dir [file normalize [file join $script_dir "work" "microblaze_system"]]
set result_dir [file normalize [file join $script_dir "results" "microblaze_system"]]
set project_dir [file normalize [file join $work_dir "project"]]
set top_name "snn_ecg_mb_full_replay_wrapper"
set part_name "xc7a100tcsg324-1"
set bd_name "snn_ecg_mb_full_replay"
set bd_tcl [file normalize [file join $repo_dir "results" "board_replay" "microblaze_full_replay" "${bd_name}_bd.tcl"]]
set constraint_file [file normalize [file join $repo_dir "constraints" "nexys_a7_microblaze_full_replay.xdc"]]

file mkdir $work_dir
file mkdir $checkpoint_dir
file mkdir $result_dir
create_project -force SNN_ECG_MB_SYSTEM_POWER $project_dir -part $part_name
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property ip_repo_paths [list [file normalize [file join $repo_dir "ip_repo"]]] [current_project]
update_ip_catalog

source $bd_tcl
set bd_file [get_files -quiet "${bd_name}.bd"]
if {[llength $bd_file] == 0} {
    set bd_file [get_files -quiet "*${bd_name}.bd"]
}
if {[llength $bd_file] == 0} {
    error "Block design was not created: $bd_name"
}
validate_bd_design
save_bd_design
generate_target all $bd_file
make_wrapper -files $bd_file -top

set wrapper_file [file normalize [file join $project_dir "SNN_ECG_MB_SYSTEM_POWER.gen" "sources_1" "bd" $bd_name "hdl" "${bd_name}_wrapper.v"]]
if {![file exists $wrapper_file]} {
    error "Generated wrapper not found: $wrapper_file"
}
add_files -norecurse [list $wrapper_file]
add_files -fileset constrs_1 [list $constraint_file]
set_property top $top_name [current_fileset]
update_compile_order -fileset sources_1

set_property strategy Flow_PerfOptimized_high [get_runs synth_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore [get_runs impl_1]

launch_runs synth_1 -jobs 4
wait_on_run synth_1
if {[get_property STATUS [get_runs synth_1]] != "synth_design Complete!"} {
    error "synth_1 failed: [get_property STATUS [get_runs synth_1]]"
}

launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    error "impl_1 failed: [get_property STATUS [get_runs impl_1]]"
}

open_run impl_1
report_utilization -file [file join $result_dir "system_utilization_post_route.rpt"]
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file [file join $result_dir "system_timing_post_route.rpt"]
report_power -file [file join $result_dir "system_power_post_route.rpt"]
write_checkpoint -force [file join $checkpoint_dir "microblaze_system_routed.dcp"]

set env_file [open [file join $result_dir "system_environment.txt"] "w"]
puts $env_file "VIVADO_VERSION=[version -short]"
puts $env_file "PART=[get_property PART [current_project]]"
puts $env_file "TOP=$top_name"
puts $env_file "IMPLEMENTATION_STATUS=[get_property STATUS [get_runs impl_1]]"
puts $env_file "CONSTRAINT=$constraint_file"
puts $env_file "ACTIVITY_SOURCE=Post-implementation vectorless Vivado power estimate; no SAIF/VCD"
puts $env_file "SWITCHING_ACTIVITY=Vivado default vectorless propagation and default toggle-rate assumptions"
foreach clk [get_clocks] {
    puts $env_file "CLOCK=$clk PERIOD_NS=[get_property PERIOD $clk]"
}
close $env_file
close_project
exit
