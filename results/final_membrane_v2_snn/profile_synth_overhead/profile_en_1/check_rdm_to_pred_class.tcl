open_checkpoint "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/profile_synth_overhead/profile_en_1/synth.dcp"
set from_cells [get_cells -hier -filter {NAME =~ *u_rdm/rdm_level_spike_reg*}]
set to_cells [get_cells -hier -filter {NAME =~ *u_class/pred_class_reg*}]
puts "FROM_COUNT=[llength $from_cells]"
puts "TO_COUNT=[llength $to_cells]"
set paths [get_timing_paths -from $from_cells -to $to_cells -max_paths 5]
puts "PATH_COUNT=[llength $paths]"
report_timing -from $from_cells -to $to_cells -max_paths 5 -file "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/profile_synth_overhead/profile_en_1/rdm_to_pred_class_timing.rpt"
exit
