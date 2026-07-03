set repo_dir "C:/Users/YangGeon/SNN ECG Classifier"
set run_dir "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/profile_synth_overhead/profile_en_0"
set env(SYNTH_COMMON) "C:/Xilinx/Vivado/2020.2/scripts/rt/data"
cd $run_dir

read_verilog [list \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/ecg_event_encoder.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/ecg_event_encoder_adaptive.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/snn_ecg_input_normalizer.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/qrs_lif_detector.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/pnn_rhythm_predictor.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/dscr_spike_counter.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/ram_peak_accumulator.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/rdm_variability_neuron.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/ectopic_pair_neuron.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/qrs_maf_neuron.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/rbbb_qrs_delay_bank.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/abandoned_feature_stubs.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/class_score_neurons.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/core/snn_ecg_3feat_top.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/final_membrane_layer.v" \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/snn_ecg_30min_final_top.v" \
]

synth_design -top snn_ecg_30min_final_top -part xc7a100tcsg324-1 \
    -mode out_of_context -flatten_hierarchy none -generic {PROFILE_EN=0}
create_clock -period 10.000 -name clk [get_ports clk]

report_utilization -file "$run_dir/utilization.rpt"
report_utilization -hierarchical -file "$run_dir/utilization_hier.rpt"
report_timing_summary -file "$run_dir/timing_summary.rpt"
set rdm_to_pred_from [get_cells -quiet -hier -filter {NAME =~ *rdm_level_spike_reg*}]
set rdm_to_pred_to [get_cells -quiet -hier -filter {NAME =~ *pred_class_reg*}]
set rdm_to_pred_paths [get_timing_paths -quiet -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 1]
if {[llength $rdm_to_pred_paths] == 0} {
    set rdm_to_pred_fp [open "$run_dir/rdm_to_pred_class_timing.rpt" w]
    puts $rdm_to_pred_fp "No timing paths found."
    close $rdm_to_pred_fp
} else {
    report_timing -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 10 -file "$run_dir/rdm_to_pred_class_timing.rpt"
}
write_checkpoint -force "$run_dir/synth.dcp"
exit
