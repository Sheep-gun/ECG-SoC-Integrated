`timescale 1ns / 1ps

module dscr_spike_counter #(
    parameter ADC_WIDTH = 12,
    parameter MEM_WIDTH = 16,
    parameter FILTER_SHIFT = 4,
    parameter FILTER_FRAC = 8,
    parameter SLOPE_INPUT_SHIFT = 0,
    parameter SLOPE_LEAK = 8,
    parameter SLOPE_THRESHOLD = 9,
    parameter SIGN_LEAK = 0,
    parameter SIGN_WEIGHT = 1,
    parameter SIGN_THRESHOLD = 1,
    parameter FAST_SLOPE_MEM_EN = 1
)(
    input clk,
    input rst,
    input clear,
    input sample_valid,
    input signed [ADC_WIDTH-1:0] adc_data,
    output reg prev_slope_valid,
    output reg prev_slope_sign,
    output reg valid_slope_spike,
    output reg sign_flip_spike
);

    localparam FILTER_WIDTH = ADC_WIDTH + FILTER_FRAC + 4;

    reg sample_seen;
    reg signed [FILTER_WIDTH-1:0] filt_mem;
    reg [MEM_WIDTH-1:0] up_mem;
    reg [MEM_WIDTH-1:0] down_mem;
    reg [MEM_WIDTH-1:0] sign_mem;

    reg signed [FILTER_WIDTH-1:0] adc_fp;
    reg signed [FILTER_WIDTH:0] filter_error;
    reg signed [FILTER_WIDTH:0] filter_update;
    reg signed [FILTER_WIDTH-1:0] filt_next;
    reg [FILTER_WIDTH:0] abs_update;
    reg [FILTER_WIDTH:0] slope_raw;
    reg [FILTER_WIDTH:0] slope_shifted;
    reg [MEM_WIDTH-1:0] slope_input;
    reg [MEM_WIDTH-1:0] up_next;
    reg [MEM_WIDTH-1:0] down_next;
    reg [MEM_WIDTH-1:0] sign_next;
    reg curr_slope_spike;
    reg curr_slope_sign;
    reg curr_sign_clear;

    localparam [MEM_WIDTH-1:0] SLOPE_LEAK_U = SLOPE_LEAK;
    localparam [MEM_WIDTH-1:0] SLOPE_THRESHOLD_U = SLOPE_THRESHOLD;
    localparam [MEM_WIDTH-1:0] SIGN_LEAK_U = SIGN_LEAK;
    localparam [MEM_WIDTH-1:0] SIGN_WEIGHT_U = SIGN_WEIGHT;
    localparam [MEM_WIDTH-1:0] SIGN_THRESHOLD_U = SIGN_THRESHOLD;

    function [MEM_WIDTH-1:0] leak_mem;
        input [MEM_WIDTH-1:0] value;
        input [MEM_WIDTH-1:0] leak;
        begin
            if (value > leak)
                leak_mem = value - leak;
            else
                leak_mem = {MEM_WIDTH{1'b0}};
        end
    endfunction

    function [MEM_WIDTH-1:0] sat_mem_add;
        input [MEM_WIDTH-1:0] value;
        input [MEM_WIDTH-1:0] add_value;
        reg [MEM_WIDTH:0] sum;
        begin
            sum = {1'b0, value} + {1'b0, add_value};
            if (sum[MEM_WIDTH])
                sat_mem_add = {MEM_WIDTH{1'b1}};
            else
                sat_mem_add = sum[MEM_WIDTH-1:0];
        end
    endfunction

    function slope_threshold_hit;
        input [MEM_WIDTH-1:0] value;
        begin
            if (SLOPE_THRESHOLD == 8)
                slope_threshold_hit = |value[MEM_WIDTH-1:3];
            else if (SLOPE_THRESHOLD == 9)
                slope_threshold_hit = (|value[MEM_WIDTH-1:4]) || (value[3] && (|value[2:0]));
            else
                slope_threshold_hit = (value >= SLOPE_THRESHOLD_U);
        end
    endfunction

    localparam USE_FAST_SLOPE_MEM = FAST_SLOPE_MEM_EN &&
                                    (MEM_WIDTH == 16) &&
                                    (SLOPE_INPUT_SHIFT == 0) &&
                                    (SLOPE_THRESHOLD == 8) &&
                                    (SLOPE_LEAK >= SLOPE_THRESHOLD);

    generate
        if (USE_FAST_SLOPE_MEM) begin : g_fast_slope_mem
            always @(posedge clk) begin
                if (rst) begin
                    sample_seen <= 1'b0;
                    filt_mem <= {FILTER_WIDTH{1'b0}};
                    up_mem <= {MEM_WIDTH{1'b0}};
                    down_mem <= {MEM_WIDTH{1'b0}};
                    sign_mem <= {MEM_WIDTH{1'b0}};
                    prev_slope_valid <= 1'b0;
                    prev_slope_sign <= 1'b0;
                    valid_slope_spike <= 1'b0;
                    sign_flip_spike <= 1'b0;
                end else begin
                    valid_slope_spike <= 1'b0;
                    sign_flip_spike <= 1'b0;

                    if (clear) begin
                        sample_seen <= 1'b0;
                        filt_mem <= {FILTER_WIDTH{1'b0}};
                        up_mem <= {MEM_WIDTH{1'b0}};
                        down_mem <= {MEM_WIDTH{1'b0}};
                        sign_mem <= {MEM_WIDTH{1'b0}};
                        prev_slope_valid <= 1'b0;
                        prev_slope_sign <= 1'b0;
                        valid_slope_spike <= 1'b0;
                        sign_flip_spike <= 1'b0;
                    end else if (sample_valid) begin
                        if (!sample_seen) begin
                            sample_seen <= 1'b1;
                            filt_mem <= {{4{adc_data[ADC_WIDTH-1]}}, adc_data, {FILTER_FRAC{1'b0}}};
                        end else begin
                            adc_fp = {{4{adc_data[ADC_WIDTH-1]}}, adc_data, {FILTER_FRAC{1'b0}}};
                            filter_error = {adc_fp[FILTER_WIDTH-1], adc_fp} -
                                           {filt_mem[FILTER_WIDTH-1], filt_mem};
                            filter_update = filter_error >>> FILTER_SHIFT;
                            filt_next = filt_mem + filter_update[FILTER_WIDTH-1:0];

                            if (filter_update[FILTER_WIDTH])
                                abs_update = (~filter_update) + 1'b1;
                            else
                                abs_update = filter_update;

                            slope_raw = abs_update >> FILTER_FRAC;
                            slope_shifted = slope_raw >> SLOPE_INPUT_SHIFT;
                            if (slope_shifted[FILTER_WIDTH:MEM_WIDTH] != {((FILTER_WIDTH + 1) - MEM_WIDTH){1'b0}})
                                slope_input = {MEM_WIDTH{1'b1}};
                            else
                                slope_input = slope_shifted[MEM_WIDTH-1:0];

                            up_next = {MEM_WIDTH{1'b0}};
                            down_next = {MEM_WIDTH{1'b0}};
                            sign_next = leak_mem(sign_mem, SIGN_LEAK_U);
                            curr_slope_spike = 1'b0;
                            curr_slope_sign = 1'b0;
                            curr_sign_clear = 1'b0;

                            if ((filter_update > 0) && (slope_input != {MEM_WIDTH{1'b0}})) begin
                                if (|slope_input[MEM_WIDTH-1:3]) begin
                                    curr_slope_spike = 1'b1;
                                    curr_slope_sign = 1'b1;
                                end else begin
                                    up_next = {{(MEM_WIDTH-3){1'b0}}, slope_input[2:0]};
                                end
                            end else if ((filter_update < 0) && (slope_input != {MEM_WIDTH{1'b0}})) begin
                                if (|slope_input[MEM_WIDTH-1:3]) begin
                                    curr_slope_spike = 1'b1;
                                    curr_slope_sign = 1'b0;
                                end else begin
                                    down_next = {{(MEM_WIDTH-3){1'b0}}, slope_input[2:0]};
                                end
                            end

                            if (curr_slope_spike) begin
                                valid_slope_spike <= 1'b1;

                                if (prev_slope_valid && (curr_slope_sign != prev_slope_sign)) begin
                                    if ((SIGN_LEAK == 0) && (SIGN_WEIGHT == 1) && (SIGN_THRESHOLD == 1)) begin
                                        sign_flip_spike <= 1'b1;
                                        curr_sign_clear = 1'b1;
                                    end else begin
                                        sign_next = sat_mem_add(sign_next, SIGN_WEIGHT_U);
                                        if (sign_next >= SIGN_THRESHOLD_U) begin
                                            sign_flip_spike <= 1'b1;
                                            curr_sign_clear = 1'b1;
                                        end
                                    end
                                end

                                prev_slope_valid <= 1'b1;
                                prev_slope_sign <= curr_slope_sign;
                            end

                            up_mem <= up_next;
                            down_mem <= down_next;
                            sign_mem <= sign_next & {MEM_WIDTH{~curr_sign_clear}};
                            filt_mem <= filt_next;
                        end
                    end
                end
            end
        end else begin : g_generic_slope_mem
            always @(posedge clk) begin
                if (rst) begin
                    sample_seen <= 1'b0;
                    filt_mem <= {FILTER_WIDTH{1'b0}};
                    up_mem <= {MEM_WIDTH{1'b0}};
                    down_mem <= {MEM_WIDTH{1'b0}};
                    sign_mem <= {MEM_WIDTH{1'b0}};
                    prev_slope_valid <= 1'b0;
                    prev_slope_sign <= 1'b0;
                    valid_slope_spike <= 1'b0;
                    sign_flip_spike <= 1'b0;
                end else begin
                    valid_slope_spike <= 1'b0;
                    sign_flip_spike <= 1'b0;

                    if (clear) begin
                        sample_seen <= 1'b0;
                        filt_mem <= {FILTER_WIDTH{1'b0}};
                        up_mem <= {MEM_WIDTH{1'b0}};
                        down_mem <= {MEM_WIDTH{1'b0}};
                        sign_mem <= {MEM_WIDTH{1'b0}};
                        prev_slope_valid <= 1'b0;
                        prev_slope_sign <= 1'b0;
                        valid_slope_spike <= 1'b0;
                        sign_flip_spike <= 1'b0;
                    end else if (sample_valid) begin
                        if (!sample_seen) begin
                            sample_seen <= 1'b1;
                            filt_mem <= {{4{adc_data[ADC_WIDTH-1]}}, adc_data, {FILTER_FRAC{1'b0}}};
                        end else begin
                            adc_fp = {{4{adc_data[ADC_WIDTH-1]}}, adc_data, {FILTER_FRAC{1'b0}}};
                            filter_error = {adc_fp[FILTER_WIDTH-1], adc_fp} -
                                           {filt_mem[FILTER_WIDTH-1], filt_mem};
                            filter_update = filter_error >>> FILTER_SHIFT;
                            filt_next = filt_mem + filter_update[FILTER_WIDTH-1:0];

                            if (filter_update[FILTER_WIDTH])
                                abs_update = (~filter_update) + 1'b1;
                            else
                                abs_update = filter_update;

                            slope_raw = abs_update >> FILTER_FRAC;
                            slope_shifted = slope_raw >> SLOPE_INPUT_SHIFT;
                            if (slope_shifted[FILTER_WIDTH:MEM_WIDTH] != {((FILTER_WIDTH + 1) - MEM_WIDTH){1'b0}})
                                slope_input = {MEM_WIDTH{1'b1}};
                            else
                                slope_input = slope_shifted[MEM_WIDTH-1:0];

                            up_next = leak_mem(up_mem, SLOPE_LEAK_U);
                            down_next = leak_mem(down_mem, SLOPE_LEAK_U);
                            sign_next = leak_mem(sign_mem, SIGN_LEAK_U);
                            curr_slope_spike = 1'b0;
                            curr_slope_sign = 1'b0;
                            curr_sign_clear = 1'b0;

                            if ((filter_update > 0) && (slope_input != {MEM_WIDTH{1'b0}})) begin
                                up_next = sat_mem_add(up_next, slope_input);
                                if (slope_threshold_hit(up_next)) begin
                                    curr_slope_spike = 1'b1;
                                    curr_slope_sign = 1'b1;
                                end
                            end else if ((filter_update < 0) && (slope_input != {MEM_WIDTH{1'b0}})) begin
                                down_next = sat_mem_add(down_next, slope_input);
                                if (slope_threshold_hit(down_next)) begin
                                    curr_slope_spike = 1'b1;
                                    curr_slope_sign = 1'b0;
                                end
                            end

                            if (curr_slope_spike) begin
                                valid_slope_spike <= 1'b1;

                                if (prev_slope_valid && (curr_slope_sign != prev_slope_sign)) begin

                                    if ((SIGN_LEAK == 0) && (SIGN_WEIGHT == 1) && (SIGN_THRESHOLD == 1)) begin

                                        sign_flip_spike <= 1'b1;

                                        curr_sign_clear = 1'b1;

                                    end else begin

                                        sign_next = sat_mem_add(sign_next, SIGN_WEIGHT_U);

                                        if (sign_next >= SIGN_THRESHOLD_U) begin

                                            sign_flip_spike <= 1'b1;

                                            curr_sign_clear = 1'b1;

                                        end

                                    end

                                end

                                prev_slope_valid <= 1'b1;
                                prev_slope_sign <= curr_slope_sign;
                            end

                            up_mem <= up_next & {MEM_WIDTH{~curr_slope_spike}};
                            down_mem <= down_next & {MEM_WIDTH{~curr_slope_spike}};
                            sign_mem <= sign_next & {MEM_WIDTH{~curr_sign_clear}};
                            filt_mem <= filt_next;
                        end
                    end
                end
            end
        end
    endgenerate

endmodule
