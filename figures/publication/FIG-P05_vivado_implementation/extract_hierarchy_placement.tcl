# Extract hierarchy-specific routed tile occupancy from the fixed Vivado DCP.
# Run from this directory:
#   vivado -mode batch -source extract_hierarchy_placement.tcl

set out_dir [pwd]
set routed_dcp "<LOCAL_VIVADO_WORK_DIR>/system_routed.dcp"

proc csv_quote {value} {
    return "\"[string map {\" \"\"} $value]\""
}

proc placement_scope {name} {
    if {[string match "*/snn_ecg_axi_accelerator_0/*" $name]} {
        return accelerator
    }
    if {[string match "*/microblaze_0_local_memory/*" $name]} {
        return local_memory
    }
    if {[string match "*/microblaze_0/*" $name]} {
        return microblaze
    }
    if {[string match "*/sample_feeder_0/*" $name]} {
        return sample_feeder
    }
    foreach pattern {
        "*/axi_uartlite_0/*"
        "*/axi_intc_0/*"
        "*/microblaze_0_axi_periph/*"
        "*/xbar_0/*"
    } {
        if {[string match $pattern $name]} {
            return control_interconnect
        }
    }
    return system_other
}

if {![file exists $routed_dcp]} {
    error "Missing routed checkpoint: $routed_dcp"
}

open_checkpoint $routed_dcp

array set occupancy {}
array set representative_tile {}
foreach cell [get_cells -quiet -hierarchical -filter {IS_PRIMITIVE == 1 && LOC != ""}] {
    set site [lindex [get_sites -quiet -of_objects $cell] 0]
    if {$site eq ""} { continue }
    set tile [lindex [get_tiles -quiet -of_objects $site] 0]
    if {$tile eq ""} { continue }
    set scope [placement_scope $cell]
    set gx [get_property GRID_POINT_X $tile]
    set gy [get_property GRID_POINT_Y $tile]
    set key "$scope,$gx,$gy"
    if {![info exists occupancy($key)]} {
        set occupancy($key) 0
        set representative_tile($key) $tile
    }
    incr occupancy($key)
}

set out_csv [file join $out_dir hierarchy_tile_occupancy.csv]
set fh [open $out_csv w]
puts $fh "scope,grid_x,grid_y,placed_primitives,representative_tile"
foreach key [lsort [array names occupancy]] {
    lassign [split $key ,] scope gx gy
    puts $fh "[csv_quote $scope],$gx,$gy,$occupancy($key),[csv_quote $representative_tile($key)]"
}
close $fh

set min_x 1000000
set max_x -1
set min_y 1000000
set max_y -1
foreach tile [get_tiles -quiet] {
    set gx [get_property GRID_POINT_X $tile]
    set gy [get_property GRID_POINT_Y $tile]
    if {$gx eq "" || $gy eq ""} { continue }
    if {$gx < $min_x} { set min_x $gx }
    if {$gx > $max_x} { set max_x $gx }
    if {$gy < $min_y} { set min_y $gy }
    if {$gy > $max_y} { set max_y $gy }
}

set bounds [open [file join $out_dir device_grid_bounds.csv] w]
puts $bounds "grid_x_min,grid_x_max,grid_y_min,grid_y_max"
puts $bounds "$min_x,$max_x,$min_y,$max_y"
close $bounds

puts "HIERARCHY_PLACEMENT_CSV=$out_csv"
puts "DEVICE_GRID_BOUNDS=$min_x,$max_x,$min_y,$max_y"
exit 0
