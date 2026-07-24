# Vivado 2020.2 reproducible export for publication Figure P05.
#
# Build/report phase:
#   vivado -mode batch -source export_vivado_figures.tcl -tclargs build
# Native vector export phase (Vivado GUI mode is required by these commands):
#   vivado -mode gui -source export_vivado_figures.tcl -tclargs vector_exports

set script_dir [file dirname [file normalize [info script]]]
set repo_root [file normalize [file join $script_dir .. ..]]
set digital_root [file join $repo_root design digital]
set source_dir [file join $digital_root results board_replay microblaze_full_replay]
set work_root [file join $repo_root artifacts vivado_figure_rebuild]
set project_dir [file join $work_root project]
set generated_routed_dcp [file join $work_root system_routed.dcp]
set archived_routed_dcp [file join $script_dir raw_vivado_evidence post_route_device system_routed.dcp]
set phase [expr {[llength $argv] > 0 ? [lindex $argv 0] : "build"}]

proc write_text_file {path body} {
    set fh [open $path w]
    puts -nonewline $fh $body
    close $fh
}

proc export_block_design {script_dir} {
    load_features ipintegrator
    set bd [get_files -quiet *.bd]
    if {[llength $bd] == 0} {
        error "No block design is open for export"
    }
    open_bd_design [lindex $bd 0]
    write_bd_layout -force -format svg -orientation landscape -scope all \
        [file join $script_dir microblaze_block_design_vivado_native.svg]
    write_bd_layout -force -format pdf -orientation landscape -scope all \
        [file join $script_dir microblaze_block_design_vivado_native.pdf]
}

proc write_accelerator_bounds {script_dir} {
    set cells [get_cells -quiet -hierarchical -filter \
        {NAME =~ */snn_ecg_axi_accelerator_0/inst/u_core/* && IS_PRIMITIVE == 1}]
    set xs {}
    set ys {}
    foreach cell $cells {
        set loc [get_property -quiet LOC $cell]
        if {[regexp {X([0-9]+)Y([0-9]+)} $loc -> x y]} {
            lappend xs $x
            lappend ys $y
        }
    }
    if {[llength $xs] == 0} {
        write_text_file [file join $script_dir accelerator_bounds.csv] \
            "xmin,xmax,ymin,ymax,placed_cells\nNA,NA,NA,NA,0\n"
        return
    }
    set xs [lsort -integer $xs]
    set ys [lsort -integer $ys]
    write_text_file [file join $script_dir accelerator_bounds.csv] \
        "xmin,xmax,ymin,ymax,placed_cells\n[lindex $xs 0],[lindex $xs end],[lindex $ys 0],[lindex $ys end],[llength $xs]\n"
}

proc csv_quote {value} {
    return "\"[string map {\" \"\"} $value]\""
}

proc write_placed_tile_occupancy {script_dir} {
    array set count {}
    array set tile_name {}
    foreach cell [get_cells -quiet -hierarchical -filter {IS_PRIMITIVE == 1 && LOC != ""}] {
        set site [lindex [get_sites -quiet -of_objects $cell] 0]
        if {$site eq ""} {
            continue
        }
        set tile [lindex [get_tiles -quiet -of_objects $site] 0]
        if {$tile eq ""} {
            continue
        }
        set scope system_other
        if {[string match "*/snn_ecg_axi_accelerator_0/inst/u_core/*" $cell]} {
            set scope accelerator_core
        }
        set gx [get_property GRID_POINT_X $tile]
        set gy [get_property GRID_POINT_Y $tile]
        set key "$scope,$gx,$gy"
        if {![info exists count($key)]} {
            set count($key) 0
            set tile_name($key) $tile
        }
        incr count($key)
    }
    set fh [open [file join $script_dir placed_tile_occupancy.csv] w]
    puts $fh "scope,grid_x,grid_y,placed_primitives,representative_tile"
    foreach key [lsort [array names count]] {
        lassign [split $key ,] scope gx gy
        puts $fh "[csv_quote $scope],$gx,$gy,$count($key),[csv_quote $tile_name($key)]"
    }
    close $fh
}

proc export_postroute_reports {routed_dcp script_dir} {
    report_timing_summary -delay_type min_max -check_timing_verbose -max_paths 50 \
        -file [file join $script_dir timing_summary.rpt]
    report_utilization -hierarchical \
        -file [file join $script_dir hierarchical_utilization.rpt]
    write_accelerator_bounds $script_dir

    set path [lindex [get_timing_paths -setup -max_paths 1 -nworst 1] 0]
    if {$path eq ""} {
        error "Vivado returned no post-route setup path"
    }
    report_timing -of_objects $path -path_type full \
        -file [file join $script_dir worst_setup_path.rpt]
    set meta "field,value\n"
    foreach {label prop} {
        startpoint STARTPOINT_PIN
        endpoint ENDPOINT_PIN
        path_delay DATAPATH_DELAY
        requirement REQUIREMENT
        slack SLACK
    } {
        append meta "$label,[get_property $prop $path]\n"
    }
    write_text_file [file join $script_dir worst_setup_path_metadata.csv] $meta
}

proc export_native_vectors {routed_dcp project_dir script_dir} {
    if {![file exists $routed_dcp]} {
        error "Routed checkpoint missing; run build phase first: $routed_dcp"
    }
    open_project [file join $project_dir SNN_ECG_P05.xpr]
    export_block_design $script_dir
    close_project

    open_checkpoint $routed_dcp
    write_placed_tile_occupancy $script_dir
    set worst [lindex [get_timing_paths -setup -max_paths 1 -nworst 1] 0]
    if {$worst eq ""} {
        error "Vivado returned no post-route setup path"
    }
    set schematic_name "P05 Worst Setup Path"
    show_schematic -name $schematic_name $worst
    after 8000
    write_schematic -force -name $schematic_name -format svg -orientation landscape -scope all \
        [file join $script_dir worst_setup_path_vivado_native.svg]
    write_schematic -force -name $schematic_name -format pdf -orientation landscape -scope all \
        [file join $script_dir worst_setup_path_vivado_native.pdf]
    write_text_file [file join $script_dir native_vector_export.txt] \
        "Vivado [version -short]\nBlock Design: write_bd_layout PDF/SVG\nWorst setup path: write_schematic PDF/SVG\nDevice View: no native PDF/SVG export in Vivado 2020.2; placed_tile_occupancy.csv is derived from routed GRID_POINT_X/Y properties.\n"
}

proc build_and_export {repo_root digital_root source_dir work_root project_dir routed_dcp script_dir} {
    file delete -force $work_root
    file mkdir $work_root

    create_project -force SNN_ECG_P05 $project_dir -part xc7a100tcsg324-1
    set_property target_language Verilog [current_project]
    set_property ip_repo_paths [list [file join $digital_root ip_repo]] [current_project]
    update_ip_catalog

    source [file join $source_dir snn_ecg_mb_full_replay_bd.tcl]
    validate_bd_design
    save_bd_design

    set bd_file [lindex [get_files -quiet *.bd] 0]
    make_wrapper -files $bd_file -top
    set wrapper [file join $project_dir SNN_ECG_P05.gen sources_1 bd \
        snn_ecg_mb_full_replay hdl snn_ecg_mb_full_replay_wrapper.v]
    puts "P05_WRAPPER=$wrapper"
    add_files -norecurse [list $wrapper]
    set_property top snn_ecg_mb_full_replay_wrapper [current_fileset]
    update_compile_order -fileset sources_1
    set constraints_file [file join $digital_root constraints nexys_a7_microblaze_full_replay.xdc]
    puts "P05_CONSTRAINTS=$constraints_file"
    add_files -fileset constrs_1 [list $constraints_file]

    generate_target all $bd_file
    export_ip_user_files -of_objects $bd_file -no_script -sync -force -quiet
    set_property strategy Flow_PerfOptimized_high [get_runs synth_1]
    set_property strategy Performance_Explore [get_runs impl_1]
    set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]
    set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE AggressiveExplore [get_runs impl_1]

    launch_runs synth_1 -jobs 4
    wait_on_run synth_1
    if {[get_property STATUS [get_runs synth_1]] ne "synth_design Complete!"} {
        error "synth_1 failed: [get_property STATUS [get_runs synth_1]]"
    }
    launch_runs impl_1 -to_step write_bitstream -jobs 4
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {
        error "impl_1 failed: [get_property STATUS [get_runs impl_1]]"
    }

    open_run impl_1
    write_checkpoint -force $routed_dcp
    export_postroute_reports $routed_dcp $script_dir

    write_text_file [file join $work_root BUILD_COMPLETE] \
        "Vivado [version -short]\nPart xc7a100tcsg324-1\nRouted checkpoint $routed_dcp\n"
    puts "P05_BUILD_COMPLETE=$routed_dcp"
}

if {$phase eq "build"} {
    build_and_export $repo_root $digital_root $source_dir $work_root \
        $project_dir $generated_routed_dcp $script_dir
    exit 0
} elseif {$phase eq "extract"} {
    set routed_dcp [expr {[file exists $generated_routed_dcp] ? $generated_routed_dcp : $archived_routed_dcp}]
    if {![file exists $routed_dcp]} {
        error "Routed checkpoint missing; run build phase first: $routed_dcp"
    }
    open_checkpoint $routed_dcp
    export_postroute_reports $routed_dcp $script_dir
    write_text_file [file join $work_root BUILD_COMPLETE] \
        "Vivado [version -short]\nPart xc7a100tcsg324-1\nRouted checkpoint $routed_dcp\n"
    exit 0
} elseif {$phase eq "vector_exports"} {
    set routed_dcp [expr {[file exists $generated_routed_dcp] ? $generated_routed_dcp : $archived_routed_dcp}]
    export_native_vectors $routed_dcp $project_dir $script_dir
    stop_gui
    exit 0
} else {
    error "Unknown phase '$phase'; use build, extract, or vector_exports"
}
