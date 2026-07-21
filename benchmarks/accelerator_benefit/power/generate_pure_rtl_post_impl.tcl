set script_dir [file dirname [file normalize [info script]]]
set repo_dir [file normalize [file join $script_dir ".." ".." ".."]]
set work_dir [file normalize [file join $script_dir "work" "pure_rtl"]]
set result_dir [file normalize [file join $script_dir "results" "pure_rtl"]]
set project_dir [file normalize [file join $work_dir "project"]]
set top_name "snn_ecg_v2_nexys_a7_top"
set part_name "xc7a100tcsg324-1"
set constraint_file [file normalize [file join $script_dir "constraints" "nexys_a7_snn_ecg_v2.xdc"]]

file mkdir $work_dir
file mkdir $result_dir
create_project -force SNN_ECG_PURE_RTL_POWER $project_dir -part $part_name
set_property target_language Verilog [current_project]
set_property include_dirs [list [file normalize [file join $repo_dir "rtl"]]] [get_filesets sources_1]

set rtl_files [list \
    [file normalize [file join $repo_dir "rtl" "core" "ecg_event_encoder.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "ecg_event_encoder_adaptive.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "snn_ecg_input_normalizer.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "qrs_lif_detector.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "pnn_rhythm_predictor.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "dscr_spike_counter.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "ram_peak_accumulator.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "rdm_variability_neuron.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "ectopic_pair_neuron.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "qrs_maf_neuron.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "rbbb_qrs_delay_bank.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "abandoned_feature_stubs.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "class_score_neurons.v"]] \
    [file normalize [file join $repo_dir "rtl" "core" "snn_ecg_3feat_top.v"]] \
    [file normalize [file join $repo_dir "rtl" "final_membrane_layer.v"]] \
    [file normalize [file join $repo_dir "rtl" "snn_ecg_30min_final_top.v"]] \
    [file normalize [file join $script_dir "sources" "snn_ecg_v2_nexys_a7_top.v"]] \
]

add_files -fileset sources_1 $rtl_files
add_files -fileset constrs_1 [list $constraint_file]
set_property top $top_name [current_fileset]
update_compile_order -fileset sources_1

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
report_utilization -file [file join $result_dir "pure_rtl_utilization_post_route.rpt"]
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file [file join $result_dir "pure_rtl_timing_post_route.rpt"]
report_power -file [file join $result_dir "pure_rtl_power_post_route.rpt"]
write_checkpoint -force [file join $work_dir "pure_rtl_routed.dcp"]

set env_file [open [file join $result_dir "pure_rtl_environment.txt"] "w"]
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
