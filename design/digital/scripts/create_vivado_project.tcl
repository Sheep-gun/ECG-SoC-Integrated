set script_dir [file dirname [file normalize [info script]]]
set repo_dir [file normalize [file join $script_dir ".."]]

set project_name "SNN_ECG_MB_FULL_REPLAY"
set project_dir [file normalize [file join $repo_dir "vivado_project" $project_name]]
set bd_name "snn_ecg_mb_full_replay"
set bd_tcl [file normalize [file join $repo_dir "results" "board_replay" "microblaze_full_replay" "${bd_name}_bd.tcl"]]
set constr_file [file normalize [file join $repo_dir "constraints" "nexys_a7_microblaze_full_replay.xdc"]]
set wrapper_dir [file normalize [file join $project_dir "hdl"]]
set wrapper_file [file normalize [file join $wrapper_dir "${bd_name}_wrapper.v"]]

if {![file exists $bd_tcl]} {
    error "Missing block design Tcl: $bd_tcl"
}
if {![file exists $constr_file]} {
    error "Missing constraint file: $constr_file"
}

file mkdir $project_dir
create_project -force $project_name $project_dir -part xc7a100tcsg324-1
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
    error "Block design was not created in project: $bd_name"
}

validate_bd_design
save_bd_design

make_wrapper -files $bd_file -top
set generated_wrapper "$project_dir/${project_name}.gen/sources_1/bd/$bd_name/hdl/${bd_name}_wrapper.v"
if {![file exists $generated_wrapper]} {
    error "Generated wrapper not found: $generated_wrapper"
}

file mkdir $wrapper_dir
file copy -force $generated_wrapper $wrapper_file
add_files -norecurse [list $wrapper_file]
set_property top ${bd_name}_wrapper [current_fileset]

add_files -fileset constrs_1 [list $constr_file]
update_compile_order -fileset sources_1
update_compile_order -fileset sim_1

set_property strategy Flow_PerfOptimized_high [get_runs synth_1]
set_property strategy Performance_Explore [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore [get_runs impl_1]

puts "XPR=$project_dir/${project_name}.xpr"
close_project
