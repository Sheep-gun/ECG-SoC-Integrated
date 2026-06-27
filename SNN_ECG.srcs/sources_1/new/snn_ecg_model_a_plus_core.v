`timescale 1ns / 1ps

module snn_ecg_model_a_plus_core #(
    parameter ADC_WIDTH = 12
)(
    input clk,
    input rst,
    input sample_valid,
    input rhythm_tick,
    input segment_start,
    input segment_done,
    input signed [ADC_WIDTH-1:0] adc_data,
    output [1:0] pred_class,
    output pred_valid
);

    // Compatibility wrapper name retained; parameters below define Snapshot C24.
    snn_ecg_3feat_top #(
        .ADC_WIDTH(ADC_WIDTH),
        .EVENT_TH(5),
        .QRS_W_EVENT(8),
        .QRS_TH(16),
        .QRS_LEAK(0),
        .QRS_REF(280),
        .ENABLE_ADAPTIVE_QRS_EVENT(1),
        .ADAPT_QRS_USE_BANK(1),
        .ADAPT_QRS_CALIB_SAMPLES(2000),
        .ADAPT_QRS_MIN_EVENT_TH(4),
        .ADAPT_QRS_PCT_TARGET(1900),
        .ADAPT_QRS_TARGET_EVENT_COUNT(100),
        .WINDOW_HALF(125),
        .DSCR_SLOPE_TH(8),
        .RAM_BANK_BASE(32),
        .RAM_BANK_STEP(32),
        .ECTOPIC_RR_TH(120),
        .RBBB_QRS_ACTIVITY_MODE(1),
        .RBBB_QRS_LOW_SLOPE_TH(5),
        .RBBB_QRS_WIDE_TH(120),
        .RBBB_QRS_TERMINAL_TH(4),
        .RBBB_QRS_REPEAT_TH(5),
        .RBBB_QRS_HIGH_RDM_SUPPRESS(0),
        .ENABLE_RBBB_QRS_DELAY_GATE(1),
        .W_RBBB_DELAY_NSR_INH(100000),
        .W_RBBB_DELAY_ARR_BOOST(100000),
        .RBBB_DELAY_CHF_OVER_ARR_BLOCK(1),
        .W_EERG_ARR_BOOST(25000),
        .EERG_PRE_QRS_BUMP_TH(1),
        .EERG_EARLY_TH(10),
        .EERG_ECP_TH(3),
        .EERG_PNN_MIS_PCT_TH(15),
        .EERG_RDM_AVG_TH(5)
    ) u_model_a_plus (
        .clk(clk),
        .rst(rst),
        .sample_valid(sample_valid),
        .rhythm_tick(rhythm_tick),
        .segment_start(segment_start),
        .segment_done(segment_done),
        .adc_data(adc_data),
        .pred_class(pred_class),
        .pred_valid(pred_valid)
    );

endmodule
