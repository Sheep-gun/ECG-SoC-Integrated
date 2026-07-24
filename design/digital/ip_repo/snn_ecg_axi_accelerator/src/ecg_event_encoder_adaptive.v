`timescale 1ns / 1ps

module ecg_event_encoder_adaptive #(
    parameter ADC_WIDTH = 12,
    parameter T_EVENT   = 20,
    parameter T_SLOPE   = 4,
    parameter ENABLE_AMP_EVENT = 0,
    parameter T_AMP_EVENT = 4,
    parameter ENABLE_ADAPTIVE = 0,
    parameter ADAPT_USE_BANK = 0,
    parameter ADAPT_CALIB_SAMPLES = 2000,
    parameter ADAPT_MIN_EVENT_TH = 4,
    parameter ADAPT_PCT_TARGET = 1900,
    parameter ADAPT_TARGET_EVENT_COUNT = 100,
    parameter BANK_TH0 = 4,
    parameter BANK_TH1 = 5,
    parameter BANK_TH2 = 6,
    parameter BANK_TH3 = 8,
    parameter BANK_TH4 = 10,
    parameter BANK_TH5 = 12,
    parameter BANK_TH6 = 16,
    parameter BANK_TH7 = 20,
    parameter BANK_TH8 = 24,
    parameter BANK_TH9 = 32,
    parameter BANK_TH10 = 40,
    parameter BANK_TH11 = 48
)(
    input clk,
    input rst,
    input sample_valid,
    input segment_start,
    input signed [ADC_WIDTH-1:0] adc_data,
    output reg signed [ADC_WIDTH-1:0] prev_sample,
    output reg signed [ADC_WIDTH:0] delta,
    output reg [ADC_WIDTH:0] abs_delta,
    output reg sample_seen,
    output reg strong_event,
    output reg up_event,
    output reg down_event,
    output reg slope_valid,
    output reg adaptive_ready,
    output reg [7:0] adaptive_event_th
);

    wire signed [ADC_WIDTH:0] adc_ext;
    wire signed [ADC_WIDTH:0] prev_ext;
    wire signed [ADC_WIDTH:0] delta_calc;
    wire [ADC_WIDTH:0] abs_delta_calc;
    wire signed [ADC_WIDTH:0] slope_pos_th;
    wire signed [ADC_WIDTH:0] slope_neg_th;
    wire [ADC_WIDTH:0] abs_adc_calc;
    wire [ADC_WIDTH:0] abs_prev_calc;
    wire amp_cross_event;
    wire [7:0] active_event_th;
    wire [5:0] hist_bin;

    reg [15:0] hist [0:63];
    reg [15:0] bank_count [0:11];
    reg [15:0] calib_count;
    integer i;
    integer scan_i;
    integer bank_i;
    reg [15:0] pct_accum;
    reg [5:0] pct_bin;
    reg pct_found;
    reg [7:0] bank_selected_th;
    reg bank_found;

    function [7:0] bank_threshold;
        input integer idx;
        begin
            case (idx)
                0: bank_threshold = BANK_TH0[7:0];
                1: bank_threshold = BANK_TH1[7:0];
                2: bank_threshold = BANK_TH2[7:0];
                3: bank_threshold = BANK_TH3[7:0];
                4: bank_threshold = BANK_TH4[7:0];
                5: bank_threshold = BANK_TH5[7:0];
                6: bank_threshold = BANK_TH6[7:0];
                7: bank_threshold = BANK_TH7[7:0];
                8: bank_threshold = BANK_TH8[7:0];
                9: bank_threshold = BANK_TH9[7:0];
                10: bank_threshold = BANK_TH10[7:0];
                default: bank_threshold = BANK_TH11[7:0];
            endcase
        end
    endfunction

    assign adc_ext = {adc_data[ADC_WIDTH-1], adc_data};
    assign prev_ext = {prev_sample[ADC_WIDTH-1], prev_sample};
    assign delta_calc = adc_ext - prev_ext;
    assign abs_delta_calc = delta_calc[ADC_WIDTH] ? ((~delta_calc) + 1'b1) : delta_calc;
    assign slope_pos_th = T_SLOPE;
    assign slope_neg_th = -T_SLOPE;
    assign abs_adc_calc = adc_ext[ADC_WIDTH] ? ((~adc_ext) + 1'b1) : adc_ext;
    assign abs_prev_calc = prev_ext[ADC_WIDTH] ? ((~prev_ext) + 1'b1) : prev_ext;
    assign amp_cross_event = ENABLE_AMP_EVENT && (abs_adc_calc > T_AMP_EVENT) && (abs_prev_calc <= T_AMP_EVENT);
    assign active_event_th = (ENABLE_ADAPTIVE && adaptive_ready) ? adaptive_event_th : T_EVENT[7:0];
    assign hist_bin = (abs_delta_calc[ADC_WIDTH:6] != 0) ? 6'd63 : abs_delta_calc[5:0];

    always @(posedge clk) begin
        if (rst) begin
            prev_sample <= {ADC_WIDTH{1'b0}};
            delta <= {(ADC_WIDTH+1){1'b0}};
            abs_delta <= {(ADC_WIDTH+1){1'b0}};
            sample_seen <= 1'b0;
            strong_event <= 1'b0;
            up_event <= 1'b0;
            down_event <= 1'b0;
            slope_valid <= 1'b0;
            adaptive_ready <= 1'b0;
            adaptive_event_th <= T_EVENT[7:0];
            calib_count <= 16'd0;
            for (i = 0; i < 64; i = i + 1)
                hist[i] <= 16'd0;
            for (i = 0; i < 12; i = i + 1)
                bank_count[i] <= 16'd0;
        end else begin
            strong_event <= 1'b0;
            up_event <= 1'b0;
            down_event <= 1'b0;
            slope_valid <= 1'b0;

            if (segment_start) begin
                adaptive_ready <= 1'b0;
                adaptive_event_th <= T_EVENT[7:0];
                calib_count <= 16'd0;
                for (i = 0; i < 64; i = i + 1)
                    hist[i] <= 16'd0;
                for (i = 0; i < 12; i = i + 1)
                    bank_count[i] <= 16'd0;
            end

            if (sample_valid) begin
                if (!sample_seen) begin
                    prev_sample <= adc_data;
                    delta <= {(ADC_WIDTH+1){1'b0}};
                    abs_delta <= {(ADC_WIDTH+1){1'b0}};
                    sample_seen <= 1'b1;
                end else begin
                    prev_sample <= adc_data;
                    delta <= delta_calc;
                    abs_delta <= abs_delta_calc;
                    strong_event <= (abs_delta_calc > active_event_th) || amp_cross_event;

                    if (delta_calc > slope_pos_th) begin
                        up_event <= 1'b1;
                        slope_valid <= 1'b1;
                    end else if (delta_calc < slope_neg_th) begin
                        down_event <= 1'b1;
                        slope_valid <= 1'b1;
                    end

                    if (ENABLE_ADAPTIVE && !adaptive_ready) begin
                        if (calib_count < ADAPT_CALIB_SAMPLES[15:0]) begin
                            hist[hist_bin] <= hist[hist_bin] + 1'b1;
                            for (bank_i = 0; bank_i < 12; bank_i = bank_i + 1) begin
                                if (abs_delta_calc > bank_threshold(bank_i))
                                    bank_count[bank_i] <= bank_count[bank_i] + 1'b1;
                            end
                            calib_count <= calib_count + 1'b1;
                        end

                        if (calib_count == (ADAPT_CALIB_SAMPLES[15:0] - 1'b1)) begin
                            if (ADAPT_USE_BANK) begin
                                bank_selected_th = BANK_TH11[7:0];
                                bank_found = 1'b0;
                                for (bank_i = 0; bank_i < 12; bank_i = bank_i + 1) begin
                                    if (!bank_found && (bank_count[bank_i] <= ADAPT_TARGET_EVENT_COUNT[15:0])) begin
                                        bank_selected_th = bank_threshold(bank_i);
                                        bank_found = 1'b1;
                                    end
                                end
                                if (bank_selected_th < ADAPT_MIN_EVENT_TH[7:0])
                                    adaptive_event_th <= ADAPT_MIN_EVENT_TH[7:0];
                                else
                                    adaptive_event_th <= bank_selected_th;
                            end else begin
                                pct_accum = 16'd0;
                                pct_bin = ADAPT_MIN_EVENT_TH[5:0];
                                pct_found = 1'b0;
                                for (scan_i = 0; scan_i < 64; scan_i = scan_i + 1) begin
                                    pct_accum = pct_accum + hist[scan_i];
                                    if (!pct_found && (pct_accum >= ADAPT_PCT_TARGET[15:0])) begin
                                        pct_bin = scan_i[5:0];
                                        pct_found = 1'b1;
                                    end
                                end
                                if (pct_bin < ADAPT_MIN_EVENT_TH[5:0])
                                    adaptive_event_th <= ADAPT_MIN_EVENT_TH[7:0];
                                else
                                    adaptive_event_th <= {2'b00, pct_bin};
                            end
                            adaptive_ready <= 1'b1;
                        end
                    end
                end
            end
        end
    end

endmodule
