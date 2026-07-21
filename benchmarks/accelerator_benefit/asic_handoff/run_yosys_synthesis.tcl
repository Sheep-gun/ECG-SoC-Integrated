# Invoke from the repository root with:
#   yosys -c benchmarks/accelerator_benefit/asic_handoff/run_yosys_synthesis.tcl
# Required environment variable: LIBERTY_FILE

if {![info exists ::env(LIBERTY_FILE)] || ![file exists $::env(LIBERTY_FILE)]} {
    error "LIBERTY_FILE must point to the target standard-cell Liberty file"
}

set top snn_ecg_30min_final_top
set sources {
    rtl/core/ecg_event_encoder.v
    rtl/core/ecg_event_encoder_adaptive.v
    rtl/core/snn_ecg_input_normalizer.v
    rtl/core/qrs_lif_detector.v
    rtl/core/pnn_rhythm_predictor.v
    rtl/core/dscr_spike_counter.v
    rtl/core/ram_peak_accumulator.v
    rtl/core/rdm_variability_neuron.v
    rtl/core/ectopic_pair_neuron.v
    rtl/core/qrs_maf_neuron.v
    rtl/core/rbbb_qrs_delay_bank.v
    rtl/core/abandoned_feature_stubs.v
    rtl/core/class_score_neurons.v
    rtl/core/snn_ecg_3feat_top.v
    rtl/final_membrane_layer.v
    rtl/snn_ecg_30min_final_top.v
}

file mkdir benchmarks/accelerator_benefit/asic_handoff/work
yosys read_liberty -lib $::env(LIBERTY_FILE)
yosys read_verilog -Irtl {*}$sources
yosys hierarchy -check -top $top
yosys synth -top $top
yosys dfflibmap -liberty $::env(LIBERTY_FILE)
yosys abc -liberty $::env(LIBERTY_FILE)
yosys clean -purge
yosys stat -liberty $::env(LIBERTY_FILE)
yosys write_verilog -noattr benchmarks/accelerator_benefit/asic_handoff/work/snn_ecg_30min_final_top_mapped.v
yosys write_json benchmarks/accelerator_benefit/asic_handoff/work/snn_ecg_30min_final_top_mapped.json
