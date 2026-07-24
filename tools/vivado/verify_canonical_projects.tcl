# Verify the two canonical Vivado projects without saving project state.

set repo_root [file normalize [file join [file dirname [info script]] ../..]]
set report_path [file join $repo_root vivado project_verification.txt]

set projects [list \
    [list pure_rtl \
        [file join $repo_root vivado pure_rtl project SNN_ECG_PURE_RTL_VISUALIZATION.xpr] \
        vivado/pure_rtl/project/SNN_ECG_PURE_RTL_VISUALIZATION.xpr \
        snn_ecg_30min_final_top \
        xc7a100tcsg324-1] \
    [list microblaze \
        [file join $repo_root vivado microblaze SNN_ECG_MB_FULL_REPLAY.xpr] \
        vivado/microblaze/SNN_ECG_MB_FULL_REPLAY.xpr \
        snn_ecg_mb_full_replay_wrapper \
        xc7a100tcsg324-1]]

set fh [open $report_path w]
puts $fh "Vivado canonical project verification"
puts $fh "Vivado version: [version -short]"

foreach project $projects {
    lassign $project label xpr rel_xpr expected_top expected_part
    if {![file exists $xpr]} {
        close $fh
        error "Missing canonical project: $xpr"
    }

    open_project -quiet $xpr
    set actual_top [get_property TOP [current_fileset]]
    set actual_part [get_property PART [current_project]]
    set source_count [llength [get_files -quiet -of_objects [get_filesets sources_1]]]

    puts $fh ""
    puts $fh "project=$label"
    puts $fh "xpr=$rel_xpr"
    puts $fh "top=$actual_top"
    puts $fh "part=$actual_part"
    puts $fh "synthesis_source_count=$source_count"

    if {$actual_top ne $expected_top} {
        close_project -quiet
        close $fh
        error "$label top mismatch: expected $expected_top, got $actual_top"
    }
    if {[string tolower $actual_part] ne [string tolower $expected_part]} {
        close_project -quiet
        close $fh
        error "$label part mismatch: expected $expected_part, got $actual_part"
    }
    if {$source_count == 0} {
        close_project -quiet
        close $fh
        error "$label has no synthesis sources"
    }

    update_compile_order -fileset sources_1
    puts $fh "status=PASS"
    close_project -quiet
}

close $fh
puts "PASS: verified two canonical Vivado projects"
puts "Report: $report_path"
