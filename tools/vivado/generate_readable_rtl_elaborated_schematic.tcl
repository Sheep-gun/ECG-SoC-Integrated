# Vivado 2020.2 visualization-only RTL elaboration flow.
#
# Batch validation:
#   vivado -mode batch -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl
#
# Automatic Vivado PDF/SVG export (GUI is started and closed automatically):
#   vivado -mode gui -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl \
#     -tclargs --auto-export-exit
#
# Interactive GUI review (schematic tabs remain open):
#   vivado -mode gui -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl \
#     -tclargs --gui

set script_dir [file dirname [file normalize [info script]]]
set repo_dir [file normalize [file join $script_dir ".." ".."]]
set artifact_dir [file normalize [file join $repo_dir "artifacts" "rtl_elaborated_schematic"]]
set project_dir [file normalize [file join $artifact_dir "vivado_project"]]
set project_name "SNN_ECG_PURE_RTL_VISUALIZATION"
set part_name "xc7a100tcsg324-1"
set top_name "snn_ecg_30min_final_top"
set rtl_dir [file normalize [file join $repo_dir "components" "digital_accelerator" "rtl"]]
set core_dir [file normalize [file join $rtl_dir "core"]]

file mkdir $artifact_dir

proc repo_path {repo_dir relative_path} {
    return [file normalize [file join $repo_dir {*}[split $relative_path "/"]]]
}

proc write_text_lines {path lines} {
    set handle [open $path "w"]
    fconfigure $handle -encoding utf-8 -translation lf
    foreach line $lines {
        puts $handle $line
    }
    close $handle
}

proc sanitize_generated_xpr {xpr_path project_name} {
    if {![file exists $xpr_path]} {
        error "Expected generated project file is missing: $xpr_path"
    }
    set handle [open $xpr_path "r"]
    set contents [read $handle]
    close $handle
    if {![regsub { Path="[^"]+\.xpr"} $contents "" sanitized]} {
        error "Could not replace generated absolute project path in XPR"
    }
    set handle [open $xpr_path "w"]
    fconfigure $handle -encoding utf-8 -translation lf
    puts -nonewline $handle $sanitized
    close $handle
}

proc require_single_cell {cell_name} {
    set cells [get_cells -quiet $cell_name]
    if {[llength $cells] != 1} {
        error "Expected exactly one elaborated cell '$cell_name', found [llength $cells]"
    }
    return [lindex $cells 0]
}

proc property_if_supported {object property_names property_name} {
    if {[lsearch -exact $property_names $property_name] >= 0} {
        return [get_property $property_name $object]
    }
    return "<unsupported>"
}

proc describe_cells {cells} {
    set result {}
    foreach cell [lsort -dictionary $cells] {
        set properties [list_property $cell]
        set ref_name [property_if_supported $cell $properties "REF_NAME"]
        set orig_ref_name [property_if_supported $cell $properties "ORIG_REF_NAME"]
        set is_primitive [property_if_supported $cell $properties "IS_PRIMITIVE"]
        set is_leaf [property_if_supported $cell $properties "IS_LEAF"]
        lappend result "CELL=$cell | REF_NAME=$ref_name | ORIG_REF_NAME=$orig_ref_name | IS_PRIMITIVE=$is_primitive | IS_LEAF=$is_leaf"
    }
    return $result
}

proc collect_existing_nets {patterns} {
    set result {}
    foreach pattern $patterns {
        set matches [get_nets -quiet -hierarchical $pattern]
        if {[llength $matches] == 0} {
            lappend result "SIGNAL=$pattern | MATCHES=0"
        } else {
            set sorted [lsort -dictionary $matches]
            set first [lindex $sorted 0]
            set last [lindex $sorted end]
            lappend result "SIGNAL=$pattern | MATCHES=[llength $sorted] | FIRST=$first | LAST=$last"
        }
    }
    return $result
}

proc require_pins {patterns} {
    set result {}
    foreach pattern $patterns {
        set matches [get_pins -quiet $pattern]
        if {[llength $matches] == 0} {
            error "No elaborated pin matched '$pattern'"
        }
        foreach pin $matches {
            lappend result $pin
        }
    }
    return [lsort -unique -dictionary $result]
}

proc require_single_pin {pin_name} {
    set matches [get_pins -quiet $pin_name]
    if {[llength $matches] != 1} {
        error "Expected exactly one elaborated pin '$pin_name', found [llength $matches]"
    }
    return [lindex $matches 0]
}

proc require_single_port {port_name} {
    set matches [get_ports -quiet $port_name]
    if {[llength $matches] != 1} {
        error "Expected exactly one elaborated port '$port_name', found [llength $matches]"
    }
    return [lindex $matches 0]
}

proc append_pin_pair {pair_variable source_pin sink_pin} {
    upvar 1 $pair_variable pairs
    lappend pairs [require_single_pin $source_pin]
    lappend pairs [require_single_pin $sink_pin]
}

proc append_port_pin_pair {pair_variable port_name pin_name} {
    upvar 1 $pair_variable pairs
    lappend pairs [require_single_port $port_name]
    lappend pairs [require_single_pin $pin_name]
}

proc append_pin_port_pair {pair_variable pin_name port_name} {
    upvar 1 $pair_variable pairs
    lappend pairs [require_single_pin $pin_name]
    lappend pairs [require_single_port $port_name]
}

set source_relpaths [list \
    "components/digital_accelerator/rtl/snn_ecg_30min_final_top.v" \
    "components/digital_accelerator/rtl/final_membrane_layer.v" \
    "components/digital_accelerator/rtl/core/snn_ecg_3feat_top.v" \
    "components/digital_accelerator/rtl/core/snn_ecg_input_normalizer.v" \
    "components/digital_accelerator/rtl/core/ecg_event_encoder_adaptive.v" \
    "components/digital_accelerator/rtl/core/qrs_lif_detector.v" \
    "components/digital_accelerator/rtl/core/pnn_rhythm_predictor.v" \
    "components/digital_accelerator/rtl/core/dscr_spike_counter.v" \
    "components/digital_accelerator/rtl/core/ram_peak_accumulator.v" \
    "components/digital_accelerator/rtl/core/rdm_variability_neuron.v" \
    "components/digital_accelerator/rtl/core/ectopic_pair_neuron.v" \
    "components/digital_accelerator/rtl/core/qrs_maf_neuron.v" \
    "components/digital_accelerator/rtl/core/rbbb_qrs_delay_bank.v" \
    "components/digital_accelerator/rtl/core/class_score_neurons.v" \
    "components/digital_accelerator/rtl/core/abandoned_feature_stubs.v" \
]

set source_files {}
foreach relative_path $source_relpaths {
    set source_file [repo_path $repo_dir $relative_path]
    if {![file exists $source_file]} {
        error "Missing required Pure RTL source: $relative_path"
    }
    lappend source_files $source_file
}

set include_file [repo_path $repo_dir "components/digital_accelerator/rtl/strict_recordwise_locked_params.vh"]
if {![file exists $include_file]} {
    error "Missing required include: components/digital_accelerator/rtl/strict_recordwise_locked_params.vh"
}

# Optional check for the committed, repository-relative disposable project.
if {[lsearch -exact $argv "--verify-existing-project"] >= 0} {
    set existing_xpr [file join $project_dir "$project_name.xpr"]
    if {![file exists $existing_xpr]} {
        error "Visualization project does not exist: $existing_xpr"
    }
    open_project $existing_xpr
    set existing_top [get_property top [get_filesets sources_1]]
    if {$existing_top ne $top_name} {
        close_project
        error "Existing visualization project has unexpected top '$existing_top'"
    }
    set forbidden_sources [get_files -quiet -regexp {(?i).*(axi|microblaze|mb_full_replay).*}]
    if {[llength $forbidden_sources] != 0} {
        close_project
        error "Existing visualization project contains forbidden AXI/MicroBlaze source files"
    }
    set existing_source_count [llength [get_files -of_objects [get_filesets sources_1]]]
    write_text_lines [file join $artifact_dir "project_open_status.txt"] [list \
        "VERIFY_EXISTING_PROJECT=PASS" \
        "TOP=$existing_top" \
        "SOURCE_COUNT=$existing_source_count" \
        "FORBIDDEN_AXI_OR_MICROBLAZE_SOURCES=0" \
    ]
    puts "VERIFY_EXISTING_PROJECT=PASS TOP=$existing_top SOURCE_COUNT=$existing_source_count"
    close_project
    exit
}

# The project is disposable. Refuse to recursively delete any directory that
# is not the exact repository-local artifact path selected above.
set expected_project_dir [file normalize [file join $repo_dir "artifacts" "rtl_elaborated_schematic" "vivado_project"]]
if {$project_dir ne $expected_project_dir} {
    error "Refusing to recreate unexpected project directory"
}
if {[file exists $project_dir]} {
    file delete -force $project_dir
}
file mkdir $project_dir

create_project -force $project_name $project_dir -part $part_name
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]

foreach source_file $source_files {
    add_files -norecurse [list $source_file]
    set added_file [get_files -quiet [list $source_file]]
    if {[llength $added_file] != 1} {
        error "Vivado did not register required source [file tail $source_file]"
    }
    set_property file_type Verilog $added_file
}
set_property include_dirs [list $rtl_dir] [get_filesets sources_1]
set_property top $top_name [get_filesets sources_1]
set_property top_auto_set 0 [get_filesets sources_1]
update_compile_order -fileset sources_1

# Confirm the project-run property exists before using it. The actual RTL
# elaboration also uses synth_design -flatten_hierarchy none, whose supported
# values are confirmed by `help synth_design` below.
set synth_run [get_runs synth_1]
set synth_run_properties [list_property $synth_run]
set flatten_run_property "STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY"
set flatten_run_property_supported [expr {[lsearch -exact $synth_run_properties $flatten_run_property] >= 0}]
if {$flatten_run_property_supported} {
    set_property $flatten_run_property none $synth_run
}

set synth_help [help synth_design]
set show_help [help show_schematic]
set write_help [help write_schematic]
set show_supported [expr {[llength [info commands show_schematic]] == 1}]
set write_supported [expr {[llength [info commands write_schematic]] == 1}]
set flatten_option_supported [expr {[string first "-flatten_hierarchy" $synth_help] >= 0 && [string first "full, none, rebuilt" $synth_help] >= 0}]
set pdf_supported [expr {$write_supported && [string first "pdf" $write_help] >= 0}]
set svg_supported [expr {$write_supported && [string first "svg" $write_help] >= 0}]
set png_supported [expr {$write_supported && [string first "png" $write_help] >= 0}]

set capability_lines [list \
    "Vivado command/property capability probe" \
    "Vivado version: [version -short]" \
    "synth_design -rtl: [expr {[string first "-rtl" $synth_help] >= 0}]" \
    "synth_design -flatten_hierarchy none: $flatten_option_supported" \
    "synth_1 run property $flatten_run_property: $flatten_run_property_supported" \
    "show_schematic command: $show_supported" \
    "write_schematic command: $write_supported" \
    "write_schematic PDF: $pdf_supported" \
    "write_schematic SVG: $svg_supported" \
    "write_schematic PNG: $png_supported" \
    "unsupported commands confirmed by help probe: export_schematic, save_schematic_pdf" \
]
write_text_lines [file join $artifact_dir "vivado_capability_report.txt"] $capability_lines

if {!$flatten_option_supported} {
    error "Vivado does not report support for synth_design -flatten_hierarchy none"
}

if {[catch {
    synth_design -rtl -name rtl_1 -top $top_name -part $part_name \
        -include_dirs [list $rtl_dir] -flatten_hierarchy none
} elaboration_error]} {
    write_text_lines [file join $artifact_dir "elaboration_error.txt"] [list $elaboration_error]
    close_project
    error "Pure RTL elaboration failed: $elaboration_error"
}

if {[current_design] eq ""} {
    close_project
    error "RTL elaboration returned without an open design"
}

set top_cell [require_single_cell "u_snapshot"]
set cell_properties [list_property $top_cell]
set required_cell_properties [list "REF_NAME" "ORIG_REF_NAME" "IS_PRIMITIVE" "IS_LEAF"]
set property_lines [list "Property support on elaborated cell u_snapshot"]
foreach property_name $required_cell_properties {
    set supported [expr {[lsearch -exact $cell_properties $property_name] >= 0}]
    set value [property_if_supported $top_cell $cell_properties $property_name]
    lappend property_lines "$property_name | supported=$supported | value=$value"
}
write_text_lines [file join $artifact_dir "cell_property_probe.txt"] $property_lines
# Vivado 2020.2 report_property is invoked directly as part of the property
# capability check. The durable, path-free subset is written above with
# list_property/get_property because the generic Tcl `redirect` command is
# not provided by this Vivado release.
report_property [get_cells u_snapshot]

if {[lsearch -exact $cell_properties "IS_PRIMITIVE"] < 0} {
    error "IS_PRIMITIVE is unavailable on elaborated cells"
}
set nonprimitive_cells [get_cells -quiet -hierarchical -filter {IS_PRIMITIVE == 0}]

set hierarchy_lines [list \
    "Vivado RTL Elaborated Design hierarchy" \
    "TOP=$top_name" \
    "PART=$part_name" \
    "FIXED_DIGITAL_COMMIT=c6b80de19cdcad5b7e43fe7835588b629d847f75" \
    "NON_PRIMITIVE_HIERARCHICAL_CELL_COUNT=[llength $nonprimitive_cells]" \
    "" \
    "TOP_MODULE=$top_name (design root; timer/control FSM are internal RTL logic, not child modules)" \
]
foreach line [describe_cells $nonprimitive_cells] {
    lappend hierarchy_lines $line
}
write_text_lines [file join $artifact_dir "hierarchy_report.txt"] $hierarchy_lines

set top_cell_names [list "u_snapshot" "u_final"]
set top_cells {}
foreach cell_name $top_cell_names {
    lappend top_cells [require_single_cell $cell_name]
}
set top_cell_lines [list \
    "Figure A selected elaborated cells" \
    "The top timer/control FSM is internal logic and is not represented as a fabricated module." \
    "SELECTED_TOP_PORTS=adc_data\[11:0\], final_valid, final_pred_class\[1:0\], final_mem_nsr/chf/arr/aff\[31:0\]" \
]
foreach line [describe_cells $top_cells] {
    lappend top_cell_lines $line
}
write_text_lines [file join $artifact_dir "selected_cells_top.txt"] $top_cell_lines

set top_net_patterns [list \
    "adc_data*" \
    "sample_valid" \
    "sample_ready" \
    "core_segment_start" \
    "core_segment_done" \
    "final_snapshot_done" \
    "final_chunk_done" \
    "c24_mem_nsr*" \
    "c24_mem_chf*" \
    "c24_mem_arr*" \
    "c24_mem_aff*" \
    "final_pred_class*" \
    "final_valid" \
    "final_mem_nsr*" \
    "final_mem_chf*" \
    "final_mem_arr*" \
    "final_mem_aff*" \
]
set top_net_lines [list \
    "Figure A selected/inspected handoff nets from the elaborated design" \
    {SCHEMATIC_SELECTION=adc_data[11:0]; c24_mem_nsr/chf/arr/aff[63:0]; final_valid; final_pred_class[1:0]; final_mem_nsr/chf/arr/aff[31:0]} \
]
foreach line [collect_existing_nets $top_net_patterns] {
    lappend top_net_lines $line
}
write_text_lines [file join $artifact_dir "selected_nets_top.txt"] $top_net_lines

set snapshot_cell_names [list \
    "u_snapshot/u_event_encoder" \
    "u_snapshot/u_qrs_detector" \
    "u_snapshot/u_pnn" \
    "u_snapshot/u_rdm" \
    "u_snapshot/u_ectopic" \
    "u_snapshot/u_dscr" \
    "u_snapshot/u_ram" \
    "u_snapshot/u_qrs_maf" \
    "u_snapshot/u_rbbb_qrs_delay" \
    "u_snapshot/u_class" \
]
set snapshot_cells {}
foreach cell_name $snapshot_cell_names {
    lappend snapshot_cells [require_single_cell $cell_name]
}
set snapshot_cell_lines [list \
    "Figure B selected principal elaborated cells" \
    "Selection is intentionally limited to 10 actual RTL instances; omitted support instances remain listed in hierarchy_report.txt." \
]
foreach line [describe_cells $snapshot_cells] {
    lappend snapshot_cell_lines $line
}
write_text_lines [file join $artifact_dir "selected_cells_snapshot.txt"] $snapshot_cell_lines

set snapshot_net_patterns [list \
    "*adc_frontend*" \
    "*strong_event*" \
    "*beat_spike*" \
    "*pnn_match_spike*" \
    "*pnn_mismatch_spike*" \
    "*dscr_sign_flip_spike*" \
    "*ram_amp_spike*" \
    "*rdm_level_spike*" \
    "*ectopic_pair_spike*" \
    "*qrs_maf_spike*" \
    "*rbbb_qrs_like_beat_spike*" \
    "c24_mem_nsr*" \
    "c24_mem_chf*" \
    "c24_mem_arr*" \
    "c24_mem_aff*" \
]
set snapshot_net_lines [list \
    "Figure B selected/inspected handoff nets from the elaborated design" \
    {SCHEMATIC_SELECTION=strong_event; beat_spike; pnn_match_spike; pnn_mismatch_spike; dscr_valid_slope_spike; dscr_sign_flip_spike; ram_amp_spike; rdm_level_spike[14:0]; ectopic_pair_spike; qrs_maf_valid_spike; rbbb_like_beat_spike} \
]
foreach line [collect_existing_nets $snapshot_net_patterns] {
    lappend snapshot_net_lines $line
}
write_text_lines [file join $artifact_dir "selected_nets_snapshot.txt"] $snapshot_net_lines

# final_membrane_layer contains no child source-module instances. Its readable
# behavior remains internal RTL logic, so Figure C is deliberately omitted.
set final_children {}
foreach cell $nonprimitive_cells {
    if {[string match "u_final/*" $cell]} {
        lappend final_children $cell
    }
}
write_text_lines [file join $artifact_dir "figure_c_decision.txt"] [list \
    "GENERATED=NO" \
    "NON_PRIMITIVE_CHILDREN_UNDER_U_FINAL=[llength $final_children]" \
    "REASON=final_membrane_layer has no child source-module instances; expanding it would expose RTL operators/registers rather than a readable module hierarchy." \
]

write_text_lines [file join $artifact_dir "batch_elaboration_status.txt"] [list \
    "ELABORATION=PASS" \
    "TOP=$top_name" \
    "PART=$part_name" \
    "FLATTEN_HIERARCHY=none" \
    "NON_PRIMITIVE_HIERARCHICAL_CELL_COUNT=[llength $nonprimitive_cells]" \
    "MICROBLAZE_OR_AXI_SOURCES_ADDED=NO" \
]

set do_gui [expr {[lsearch -exact $argv "--gui"] >= 0 || [lsearch -exact $argv "--auto-export-exit"] >= 0}]
set auto_exit [expr {[lsearch -exact $argv "--auto-export-exit"] >= 0}]

if {$do_gui} {
    if {!$show_supported || !$write_supported || !$pdf_supported || !$svg_supported} {
        error "Vivado GUI schematic PDF/SVG export commands are not fully supported"
    }

    set fig_a_name "FIG-RTL-A_top_hierarchy"
    set fig_b_name "FIG-RTL-B_snapshot_core_hierarchy"

    # Pin-pair mode limits each hierarchy box to the actual reader-facing
    # input/output and handoff pins instead of expanding every debug port.
    set fig_a_pin_pairs {}
    append_port_pin_pair fig_a_pin_pairs {adc_data[0]} {u_snapshot/adc_data[0]}
    append_pin_pair fig_a_pin_pairs {u_snapshot/c24_mem_nsr[0]} {u_final/class_mem_nsr[0]}
    append_pin_pair fig_a_pin_pairs {u_snapshot/c24_mem_chf[0]} {u_final/class_mem_chf[0]}
    append_pin_pair fig_a_pin_pairs {u_snapshot/c24_mem_arr[0]} {u_final/class_mem_arr[0]}
    append_pin_pair fig_a_pin_pairs {u_snapshot/c24_mem_aff[0]} {u_final/class_mem_aff[0]}
    append_pin_port_pair fig_a_pin_pairs {u_final/final_valid} {final_valid}
    append_pin_port_pair fig_a_pin_pairs {u_final/final_pred_class[0]} {final_pred_class[0]}
    append_pin_port_pair fig_a_pin_pairs {u_final/final_mem_nsr[0]} {final_mem_nsr[0]}
    append_pin_port_pair fig_a_pin_pairs {u_final/final_mem_chf[0]} {final_mem_chf[0]}
    append_pin_port_pair fig_a_pin_pairs {u_final/final_mem_arr[0]} {final_mem_arr[0]}
    append_pin_port_pair fig_a_pin_pairs {u_final/final_mem_aff[0]} {final_mem_aff[0]}
    show_schematic -pin_pairs -name $fig_a_name $fig_a_pin_pairs
    show_schematic -pin_pairs -name $fig_a_name -regenerate $fig_a_pin_pairs
    write_schematic -force -format pdf -orientation landscape -scope all -name $fig_a_name \
        [file join $artifact_dir "FIG-RTL-A_top_hierarchy.pdf"]
    write_schematic -force -format svg -orientation landscape -scope all -name $fig_a_name \
        [file join $artifact_dir "FIG-RTL-A_top_hierarchy.svg"]

    if {[lsearch -exact $argv "--figure-a-only"] < 0} {
        set fig_b_pin_pairs {}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_event_encoder/strong_event} {u_snapshot/u_qrs_detector/strong_event}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_event_encoder/strong_event} {u_snapshot/u_qrs_maf/strong_event}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_event_encoder/strong_event} {u_snapshot/u_rbbb_qrs_delay/strong_event}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_qrs_detector/beat_spike} {u_snapshot/u_pnn/beat_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_qrs_detector/beat_spike} {u_snapshot/u_ram/beat_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_qrs_detector/beat_spike} {u_snapshot/u_qrs_maf/beat_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_pnn/pnn_match_spike} {u_snapshot/u_class/pnn_match_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_pnn/pnn_mismatch_spike} {u_snapshot/u_class/pnn_mismatch_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_dscr/valid_slope_spike} {u_snapshot/u_class/dscr_valid_slope_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_dscr/sign_flip_spike} {u_snapshot/u_class/dscr_sign_flip_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_ram/ram_amp_spike} {u_snapshot/u_class/ram_amp_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_rdm/rdm_level_spike[0]} {u_snapshot/u_class/rdm_level_spike[0]}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_ectopic/ectopic_pair_spike} {u_snapshot/u_class/ectopic_pair_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_qrs_maf/qrs_maf_valid_spike} {u_snapshot/u_class/qrs_maf_valid_spike}
        append_pin_pair fig_b_pin_pairs {u_snapshot/u_rbbb_qrs_delay/rbbb_like_beat_spike} {u_snapshot/u_class/rbbb_qrs_like_beat_spike}
        show_schematic -pin_pairs -name $fig_b_name $fig_b_pin_pairs
        show_schematic -pin_pairs -name $fig_b_name -regenerate $fig_b_pin_pairs
        write_schematic -force -format pdf -orientation landscape -scope all -name $fig_b_name \
            [file join $artifact_dir "FIG-RTL-B_snapshot_core_hierarchy.pdf"]
        write_schematic -force -format svg -orientation landscape -scope all -name $fig_b_name \
            [file join $artifact_dir "FIG-RTL-B_snapshot_core_hierarchy.svg"]

    }

    write_text_lines [file join $artifact_dir "automatic_export_status.txt"] [list \
        "VIVADO_PDF_EXPORT=PASS" \
        "VIVADO_SVG_EXPORT=PASS" \
        "VIVADO_NATIVE_PNG_EXPORT=UNSUPPORTED" \
        "FIGURE_C=NOT_GENERATED" \
    ]

    if {$auto_exit} {
        close_project
        sanitize_generated_xpr [file join $project_dir "$project_name.xpr"] $project_name
        exit
    }
} else {
    if {![file exists [file join $artifact_dir "automatic_export_status.txt"]]} {
        write_text_lines [file join $artifact_dir "automatic_export_status.txt"] [list \
            "VIVADO_PDF_EXPORT=NOT_RUN_IN_BATCH_MODE" \
            "VIVADO_SVG_EXPORT=NOT_RUN_IN_BATCH_MODE" \
            "VIVADO_NATIVE_PNG_EXPORT=UNSUPPORTED" \
            "RUN_GUI_COMMAND=vivado -mode gui -source tools/vivado/generate_readable_rtl_elaborated_schematic.tcl -tclargs --auto-export-exit" \
            "FIGURE_C=NOT_GENERATED" \
        ]
    }
    close_project
    sanitize_generated_xpr [file join $project_dir "$project_name.xpr"] $project_name
    exit
}
