set repo_dir "C:/Users/YangGeon/SNN ECG Classifier"
set run_dir "C:/Users/YangGeon/SNN ECG Classifier/results/final_membrane_v2_snn/axi_impl_timing_10ns/profile_en_1"
set env(SYNTH_COMMON) "C:/Xilinx/Vivado/2020.2/scripts/rt/data"
cd $run_dir

read_verilog [list \
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/common/reset_sync.v" \
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
    "C:/Users/YangGeon/SNN ECG Classifier/rtl/axi/snn_ecg_axi_lite_stream_top.v" \
]
read_xdc [list "C:/Users/YangGeon/SNN ECG Classifier/constraints/snn_ecg_axi_ooc.xdc"]

synth_design -top snn_ecg_axi_lite_stream_top -part xc7a100tcsg324-1 \
    -mode out_of_context -flatten_hierarchy none -generic {PROFILE_EN=1}
report_timing_summary -file "$run_dir/post_synth_timing_summary.rpt"
check_timing -verbose -file "$run_dir/post_synth_check_timing.rpt"

opt_design
place_design
phys_opt_design
route_design

report_route_status -file "$run_dir/route_status.rpt"
check_timing -verbose -file "$run_dir/post_route_check_timing.rpt"
report_timing_summary -file "$run_dir/post_route_timing_summary.rpt"
report_timing -delay_type max -max_paths 30 -nworst 5 \
    -path_type full_clock_expanded -input_pins \
    -file "$run_dir/worst_setup_paths.rpt"
report_timing -delay_type min -max_paths 30 -nworst 5 \
    -path_type full_clock_expanded -input_pins \
    -file "$run_dir/worst_hold_paths.rpt"
report_utilization -file "$run_dir/post_route_utilization.rpt"
report_utilization -hierarchical -file "$run_dir/post_route_utilization_hier.rpt"
report_clock_utilization -file "$run_dir/clock_utilization.rpt"
catch {report_cdc -details -file "$run_dir/cdc.rpt"} cdc_err
catch {report_clock_interaction -file "$run_dir/clock_interaction.rpt"} clock_interaction_err
catch {report_io -file "$run_dir/io.rpt"} io_err
catch {report_control_sets -file "$run_dir/control_sets.rpt"} control_sets_err
catch {report_methodology -file "$run_dir/methodology.rpt"} methodology_err
catch {report_drc -file "$run_dir/drc.rpt"} drc_err
catch {report_qor_suggestions -file "$run_dir/qor_suggestions.rpt"} qor_err

set rdm_to_pred_from [get_cells -quiet -hier -filter {NAME =~ *rdm_level_spike_reg*}]
set rdm_to_pred_to [get_cells -quiet -hier -filter {NAME =~ *pred_class_reg*}]
set rdm_to_pred_paths [get_timing_paths -quiet -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 1]
if {[llength $rdm_to_pred_paths] == 0} {
    set rdm_to_pred_fp [open "$run_dir/rdm_to_pred_class_timing.rpt" w]
    puts $rdm_to_pred_fp "No timing paths found."
    close $rdm_to_pred_fp
} else {
    report_timing -from $rdm_to_pred_from -to $rdm_to_pred_to -max_paths 10 \
        -path_type full_clock_expanded -input_pins \
        -file "$run_dir/rdm_to_pred_class_timing.rpt"
}

write_checkpoint -force "$run_dir/routed.dcp"
exit
