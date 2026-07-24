# Vivado 2020.2 batch validation for the archived routed checkpoints.

set script_dir [file dirname [file normalize [info script]]]
set checkpoints [list \
    [file join $script_dir post_route_device system_routed.dcp] \
    [file join $script_dir system_power system_power_routed.dcp]]

foreach checkpoint $checkpoints {
    if {![file exists $checkpoint]} {
        error "Missing archived checkpoint: $checkpoint"
    }
    open_checkpoint $checkpoint
    set worst [lindex [get_timing_paths -setup -max_paths 1 -nworst 1] 0]
    set slack [expr {$worst eq "" ? "NA" : [get_property SLACK $worst]}]
    puts "ARCHIVED_DCP_OK=[file tail $checkpoint]"
    puts "PART=[get_property PART [current_design]]"
    puts "TOP=[current_design]"
    puts "WORST_SETUP_SLACK=$slack"
    close_design
}

exit 0
