if {$argc != 6} {
    error "Usage: report_activity_power.tcl <dcp> <saif> <strip_path> <output_dir> <prefix> <activity_description>"
}
set dcp_file [file normalize [lindex $argv 0]]
set saif_file [file normalize [lindex $argv 1]]
set strip_path [lindex $argv 2]
set output_dir [file normalize [lindex $argv 3]]
set prefix [lindex $argv 4]
set activity_description [lindex $argv 5]

if {![file exists $dcp_file]} { error "Missing routed checkpoint: $dcp_file" }
if {![file exists $saif_file]} { error "Missing SAIF: $saif_file" }
file mkdir $output_dir
open_checkpoint $dcp_file

# The testbench drives reset low only during initialization; keep reset pins
# deasserted for any nodes that cannot be matched from RTL SAIF to post-route.
set_switching_activity -deassert_resets
set unmatched_file [file join $output_dir "${prefix}_saif_unmatched.rpt"]
read_saif -verbose -strip_path $strip_path -out_file $unmatched_file $saif_file

report_power -hier all -hierarchical_depth 0 -file [file join $output_dir "${prefix}_power_post_route.rpt"]
report_utilization -file [file join $output_dir "${prefix}_utilization_post_route.rpt"]
report_timing_summary -delay_type min_max -max_paths 20 -file [file join $output_dir "${prefix}_timing_post_route.rpt"]

set all_registers [get_cells -hierarchical -filter {PRIMITIVE_GROUP == FLOP_LATCH}]
set ce_pins [get_pins -of_objects $all_registers -filter {REF_PIN_NAME == CE}]
set ce_nonconstant 0
foreach ce_pin $ce_pins {
    set ce_net [get_nets -quiet -of_objects $ce_pin]
    if {[llength $ce_net] > 0} {
        set drivers [get_pins -quiet -leaf -of_objects $ce_net -filter {DIRECTION == OUT}]
        if {[llength $drivers] > 0} {
            incr ce_nonconstant
        }
    }
}

set env_file [open [file join $output_dir "${prefix}_environment.txt"] "w"]
puts $env_file "VIVADO_VERSION=[version -short]"
puts $env_file "PART=[get_property PART [current_design]]"
puts $env_file "TOP=[get_property TOP [current_design]]"
puts $env_file "IMPLEMENTATION_STATUS=routed"
puts $env_file "DCP=$dcp_file"
puts $env_file "SAIF=$saif_file"
puts $env_file "SAIF_STRIP_PATH=$strip_path"
puts $env_file "ACTIVITY_SOURCE=$activity_description"
puts $env_file "RESET_POLICY=set_switching_activity -deassert_resets before read_saif"
puts $env_file "REGISTER_PRIMITIVES=[llength $all_registers]"
puts $env_file "REGISTER_CE_PINS=[llength $ce_pins]"
puts $env_file "REGISTER_CE_PINS_WITH_DRIVEN_NET=$ce_nonconstant"
foreach clk [get_clocks] {
    puts $env_file "CLOCK=$clk PERIOD_NS=[get_property PERIOD $clk]"
}
close $env_file
close_design
exit
