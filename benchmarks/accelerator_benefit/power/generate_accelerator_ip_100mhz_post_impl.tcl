set script_dir [file dirname [file normalize [info script]]]
set repo_dir [file normalize [file join $script_dir ".." ".." ".."]]
set work_dir [file normalize [file join $script_dir "work" "accelerator_ip_100mhz"]]
set result_root [file normalize [file join $script_dir "results"]]
set baseline_result [file join $result_root "accelerator_ip_100mhz"]
set power_opt_result [file join $result_root "accelerator_ip_100mhz_power_opt"]
set project_dir [file join $work_dir "project"]
set top_name "snn_ecg_accelerator_power_top"
set part_name "xc7a100tcsg324-1"
set constraint_file [file normalize [file join $script_dir "constraints" "snn_ecg_accelerator_100mhz.xdc"]]

file mkdir $work_dir
file mkdir $baseline_result
file mkdir $power_opt_result
create_project -force SNN_ECG_ACCELERATOR_IP_POWER $project_dir -part $part_name
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
    [file normalize [file join $script_dir "sources" "snn_ecg_accelerator_power_top.v"]] \
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
set_property strategy Performance_Explore [get_runs impl_1]
launch_runs impl_1 -to_step route_design -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    error "impl_1 failed: [get_property STATUS [get_runs impl_1]]"
}
open_run impl_1
set base_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
if {$base_wns < 0.0} {
    phys_opt_design -directive AggressiveExplore
    route_design -directive Explore
    set base_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
}
report_utilization -file [file join $baseline_result "accelerator_ip_100mhz_utilization_post_route.rpt"]
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file [file join $baseline_result "accelerator_ip_100mhz_timing_post_route.rpt"]
report_power -file [file join $baseline_result "accelerator_ip_100mhz_vectorless_power_post_route.rpt"]
write_checkpoint -force [file join $work_dir "accelerator_ip_100mhz_routed.dcp"]
close_design

set synth_dcp [file join $project_dir "SNN_ECG_ACCELERATOR_IP_POWER.runs" "synth_1" "${top_name}.dcp"]
open_checkpoint $synth_dcp
source $constraint_file
opt_design
power_opt_design
report_power_opt -file [file join $power_opt_result "accelerator_ip_100mhz_power_opt_transformations.rpt"]
place_design
phys_opt_design
route_design
set opt_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
if {$opt_wns < 0.0} {
    phys_opt_design -directive AggressiveExplore
    route_design -directive Explore
    set opt_wns [get_property SLACK [get_timing_paths -delay_type max -max_paths 1]]
}
report_utilization -file [file join $power_opt_result "accelerator_ip_100mhz_power_opt_utilization_post_route.rpt"]
report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 -file [file join $power_opt_result "accelerator_ip_100mhz_power_opt_timing_post_route.rpt"]
report_power -file [file join $power_opt_result "accelerator_ip_100mhz_power_opt_vectorless_power_post_route.rpt"]
write_checkpoint -force [file join $work_dir "accelerator_ip_100mhz_power_opt_routed.dcp"]

set env_file [open [file join $baseline_result "accelerator_ip_100mhz_environment.txt"] "w"]
puts $env_file "VIVADO_VERSION=[version -short]"
puts $env_file "PART=[get_property PART [current_design]]"
puts $env_file "TOP=$top_name"
puts $env_file "TIMING_STATUS=[expr {$base_wns >= 0.0 ? {MET} : {FAILED}}]"
puts $env_file "WNS_NS=$base_wns"
puts $env_file "CONSTRAINT=$constraint_file"
puts $env_file "SCOPE=Locked accelerator RTL only; excludes LFSR, LED, MicroBlaze, UART, sample memory and board peripherals"
close $env_file
set env_file [open [file join $power_opt_result "accelerator_ip_100mhz_power_opt_environment.txt"] "w"]
puts $env_file "VIVADO_VERSION=[version -short]"
puts $env_file "PART=[get_property PART [current_design]]"
puts $env_file "TOP=$top_name"
puts $env_file "TIMING_STATUS=[expr {$opt_wns >= 0.0 ? {MET} : {FAILED}}]"
puts $env_file "WNS_NS=$opt_wns"
puts $env_file "CONSTRAINT=$constraint_file"
puts $env_file "SCOPE=Locked accelerator RTL only with Vivado power_opt_design; no functional RTL change"
close $env_file
close_design
close_project
exit
