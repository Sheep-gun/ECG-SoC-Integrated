`timescale 1ns / 1ps



module qrs_maf_neuron #(

    parameter ADC_WIDTH = 12,

    parameter CODE_WIDTH = 6,

    parameter WIN_WIDTH = 8,

    parameter PRE_WIN = 120,

    parameter POST_WIN = 100,

    parameter WIDTH_TH = 120,

    parameter WIDTH_DEV_TH = 40,

    parameter COMPLEX_TH = 6,

    parameter ENERGY_SHIFT = 5,

    parameter ENERGY_DEV_TH = 8,

    parameter REF_SHIFT = 3

)(

    input clk,

    input rst,

    input clear,

    input sample_valid,

    input signed [ADC_WIDTH-1:0] adc_data,

    input signed [ADC_WIDTH-1:0] baseline,

    input strong_event,

    input dscr_sign_flip_spike,

    input beat_spike,

    output reg qrs_maf_valid_spike,

    output reg qrs_width_abn_spike,

    output reg qrs_complex_abn_spike,

    output reg qrs_energy_abn_spike,

    output reg pre_qrs_bump_spike,

    output reg [7:0] qrs_width_value,

    output reg [CODE_WIDTH-1:0] qrs_complex_count,

    output reg [CODE_WIDTH-1:0] qrs_energy_code

);



    localparam [WIN_WIDTH-1:0] POST_WIN_U = POST_WIN;

    localparam [7:0] PRE_WIN_U = PRE_WIN;

    localparam [7:0] WIDTH_TH_U = WIDTH_TH;

    localparam [7:0] WIDTH_DEV_TH_U = WIDTH_DEV_TH;

    localparam [CODE_WIDTH-1:0] COMPLEX_TH_U = COMPLEX_TH;

    localparam [CODE_WIDTH-1:0] ENERGY_DEV_TH_U = ENERGY_DEV_TH;

    localparam [CODE_WIDTH-1:0] CODE_MAX = {CODE_WIDTH{1'b1}};


    function [7:0] pre_fifo_ptr_next;

        input [7:0] ptr;

        begin

            if (ptr == (PRE_WIN_U - 8'd1))

                pre_fifo_ptr_next = 8'd0;

            else

                pre_fifo_ptr_next = ptr + 8'd1;

        end

    endfunction



    reg [PRE_WIN-1:0] pre_strong_sr;

    reg [PRE_WIN-1:0] pre_flip_sr;

    reg [7:0] pre_energy_sr [0:PRE_WIN-1];

    reg [7:0] pre_strong_count;

    reg [7:0] pre_flip_count;

    reg [15:0] pre_energy_sum;

    (* ram_style = "distributed" *) reg [7:0] pre_strong_time_fifo [0:PRE_WIN-1];

    reg [7:0] pre_strong_head;

    reg [7:0] pre_strong_tail;

    reg [7:0] pre_sample_idx;

    reg [7:0] pre_oldest_time;

    reg [7:0] pre_newest_time;



    reg window_active;

    reg [WIN_WIDTH-1:0] post_count;

    reg event_seen;

    reg [7:0] first_pos;

    reg [7:0] last_pos;

    reg [7:0] event_count;

    reg [7:0] flip_count;

    reg [15:0] energy_sum;

    reg [7:0] pre_strong_at_beat;

    reg [7:0] pre_flip_at_beat;

    reg [15:0] pre_energy_at_beat;

    reg [7:0] width_ref;

    reg [CODE_WIDTH-1:0] energy_ref;

    reg width_ref_valid;

    reg energy_ref_valid;



    reg pre_seen_comb;

    reg [7:0] pre_first_comb;

    reg [7:0] pre_last_comb;

    reg pre_strong_pop_comb;

    reg [7:0] pre_strong_head_next_comb;

    reg [7:0] pre_strong_tail_next_comb;

    reg [7:0] pre_strong_count_next_comb;

    reg [7:0] pre_oldest_age_comb;

    reg [7:0] pre_newest_age_comb;

    reg [7:0] pre_oldest_time_next_comb;

    reg [7:0] pre_newest_time_next_comb;

    reg event_seen_eval;

    reg [7:0] first_pos_eval;

    reg [7:0] last_pos_eval;

    reg [7:0] width_eval;

    reg [7:0] width_diff_abs;

    reg [7:0] flip_count_eval;

    reg [15:0] energy_sum_eval;

    reg signed [ADC_WIDTH:0] adc_ext;

    reg signed [ADC_WIDTH:0] base_ext;

    reg [15:0] energy_sample_abs;

    reg [7:0] energy_sample_code;

    reg [15:0] energy_shifted;

    reg [CODE_WIDTH-1:0] energy_code_next;

    reg [CODE_WIDTH-1:0] energy_diff_abs;

    reg [CODE_WIDTH-1:0] complex_next;

    reg qrs_eval_pending;

    reg qrs_eval_cond_pending;

    reg [7:0] qrs_eval_width_reg;

    reg [CODE_WIDTH-1:0] qrs_eval_complex_reg;

    reg [CODE_WIDTH-1:0] qrs_eval_energy_reg;

    reg [7:0] qrs_eval_width_ref_reg;

    reg qrs_eval_width_ref_valid_reg;

    reg [CODE_WIDTH-1:0] qrs_eval_energy_ref_reg;

    reg qrs_eval_energy_ref_valid_reg;

    reg [7:0] qrs_eval_width_diff_abs;

    reg [CODE_WIDTH-1:0] qrs_eval_energy_diff_abs;

    reg qrs_eval_wide_reg;

    reg qrs_eval_complex_cond_reg;

    reg qrs_eval_energy_cond_reg;

    reg qrs_eval_pre_bump_reg;

    integer i;



    always @* begin

        pre_seen_comb = (pre_strong_count != 8'd0);

        pre_oldest_age_comb = pre_sample_idx - pre_oldest_time;

        pre_newest_age_comb = pre_sample_idx - pre_newest_time;

        pre_first_comb = pre_seen_comb ? (PRE_WIN_U - pre_oldest_age_comb) : 8'd0;

        pre_last_comb = pre_seen_comb ? (PRE_WIN_U - pre_newest_age_comb) : 8'd0;

        pre_strong_pop_comb = pre_strong_sr[PRE_WIN-1];

        pre_strong_head_next_comb = pre_fifo_ptr_next(pre_strong_head);

        pre_strong_tail_next_comb = pre_fifo_ptr_next(pre_strong_tail);

        pre_strong_count_next_comb = pre_strong_count + {7'd0, strong_event} - {7'd0, pre_strong_pop_comb};

        pre_oldest_time_next_comb = pre_oldest_time;

        pre_newest_time_next_comb = pre_newest_time;

        if (pre_strong_count_next_comb == 8'd0) begin

            pre_oldest_time_next_comb = 8'd0;

            pre_newest_time_next_comb = 8'd0;

        end else begin

            if (pre_strong_count == 8'd0)

                pre_oldest_time_next_comb = pre_sample_idx;

            else if (pre_strong_pop_comb) begin

                if (pre_strong_count == 8'd1)

                    pre_oldest_time_next_comb = strong_event ? pre_sample_idx : 8'd0;

                else

                    pre_oldest_time_next_comb = pre_strong_time_fifo[pre_strong_head_next_comb];

            end



            if (strong_event)

                pre_newest_time_next_comb = pre_sample_idx;

        end



        adc_ext = {adc_data[ADC_WIDTH-1], adc_data};

        base_ext = {baseline[ADC_WIDTH-1], baseline};

        if (adc_ext >= base_ext)

            energy_sample_abs = adc_ext - base_ext;

        else

            energy_sample_abs = base_ext - adc_ext;



        energy_shifted = energy_sample_abs >> ENERGY_SHIFT;

        if (energy_shifted[15:8] != 8'd0)

            energy_sample_code = 8'hff;

        else

            energy_sample_code = energy_shifted[7:0];



        event_seen_eval = event_seen || strong_event;

        first_pos_eval = first_pos;

        if (!event_seen && strong_event)

            first_pos_eval = PRE_WIN_U + post_count;

        last_pos_eval = strong_event ? (PRE_WIN_U + post_count) : last_pos;



        if (event_seen_eval)

            width_eval = last_pos_eval - first_pos_eval;

        else

            width_eval = 8'd0;



        if (width_eval >= width_ref)

            width_diff_abs = width_eval - width_ref;

        else

            width_diff_abs = width_ref - width_eval;



        flip_count_eval = flip_count + {7'd0, dscr_sign_flip_spike};

        if (energy_sum <= (16'hffff - {8'd0, energy_sample_code}))

            energy_sum_eval = energy_sum + {8'd0, energy_sample_code};

        else

            energy_sum_eval = 16'hffff;



        energy_shifted = energy_sum_eval >> 6;

        if (energy_shifted > {10'd0, CODE_MAX})

            energy_code_next = CODE_MAX;

        else

            energy_code_next = energy_shifted[CODE_WIDTH-1:0];



        if (energy_code_next >= energy_ref)

            energy_diff_abs = energy_code_next - energy_ref;

        else

            energy_diff_abs = energy_ref - energy_code_next;



        if (flip_count_eval > {2'd0, CODE_MAX})

            complex_next = CODE_MAX;

        else

            complex_next = flip_count_eval[CODE_WIDTH-1:0];



    end

    always @* begin

        if (qrs_eval_width_reg >= qrs_eval_width_ref_reg)

            qrs_eval_width_diff_abs = qrs_eval_width_reg - qrs_eval_width_ref_reg;

        else

            qrs_eval_width_diff_abs = qrs_eval_width_ref_reg - qrs_eval_width_reg;

        if (qrs_eval_energy_reg >= qrs_eval_energy_ref_reg)

            qrs_eval_energy_diff_abs = qrs_eval_energy_reg - qrs_eval_energy_ref_reg;

        else

            qrs_eval_energy_diff_abs = qrs_eval_energy_ref_reg - qrs_eval_energy_reg;

    end



    always @(posedge clk) begin

        if (rst) begin

            pre_strong_sr <= {PRE_WIN{1'b0}};

            pre_flip_sr <= {PRE_WIN{1'b0}};

            pre_strong_count <= 8'd0;

            pre_flip_count <= 8'd0;

            pre_energy_sum <= 16'd0;

            pre_strong_head <= 8'd0;

            pre_strong_tail <= 8'd0;

            pre_sample_idx <= 8'd0;

            pre_oldest_time <= 8'd0;

            pre_newest_time <= 8'd0;

            for (i = 0; i < PRE_WIN; i = i + 1)

                pre_energy_sr[i] <= 8'd0;

            window_active <= 1'b0;

            post_count <= {WIN_WIDTH{1'b0}};

            event_seen <= 1'b0;

            first_pos <= 8'd0;

            last_pos <= 8'd0;

            event_count <= 8'd0;

            flip_count <= 8'd0;

            energy_sum <= 16'd0;

            pre_strong_at_beat <= 8'd0;

            pre_flip_at_beat <= 8'd0;

            pre_energy_at_beat <= 16'd0;

            width_ref <= 8'd0;

            energy_ref <= {CODE_WIDTH{1'b0}};

            width_ref_valid <= 1'b0;

            energy_ref_valid <= 1'b0;

            qrs_maf_valid_spike <= 1'b0;

            qrs_width_abn_spike <= 1'b0;

            qrs_complex_abn_spike <= 1'b0;

            qrs_energy_abn_spike <= 1'b0;

            pre_qrs_bump_spike <= 1'b0;

            pre_qrs_bump_spike <= 1'b0;

            qrs_width_value <= 8'd0;

            qrs_complex_count <= {CODE_WIDTH{1'b0}};

            qrs_energy_code <= {CODE_WIDTH{1'b0}};

            qrs_eval_pending <= 1'b0;

            qrs_eval_cond_pending <= 1'b0;

            qrs_eval_width_reg <= 8'd0;

            qrs_eval_complex_reg <= {CODE_WIDTH{1'b0}};

            qrs_eval_energy_reg <= {CODE_WIDTH{1'b0}};

            qrs_eval_width_ref_reg <= 8'd0;

            qrs_eval_width_ref_valid_reg <= 1'b0;

            qrs_eval_energy_ref_reg <= {CODE_WIDTH{1'b0}};

            qrs_eval_energy_ref_valid_reg <= 1'b0;

            qrs_eval_wide_reg <= 1'b0;

            qrs_eval_complex_cond_reg <= 1'b0;

            qrs_eval_energy_cond_reg <= 1'b0;

            qrs_eval_pre_bump_reg <= 1'b0;

        end else begin

            qrs_maf_valid_spike <= 1'b0;

            qrs_width_abn_spike <= 1'b0;

            qrs_complex_abn_spike <= 1'b0;

            qrs_energy_abn_spike <= 1'b0;

            pre_qrs_bump_spike <= 1'b0;



            if (qrs_eval_pending) begin

                qrs_eval_pending <= 1'b0;

                qrs_maf_valid_spike <= 1'b1;

                qrs_width_value <= qrs_eval_width_reg;

                qrs_complex_count <= qrs_eval_complex_reg;

                qrs_energy_code <= qrs_eval_energy_reg;

                qrs_width_abn_spike <= qrs_eval_wide_reg;

                qrs_complex_abn_spike <= qrs_eval_complex_cond_reg;

                qrs_energy_abn_spike <= qrs_eval_energy_cond_reg;

                pre_qrs_bump_spike <= qrs_eval_pre_bump_reg;

                if (!width_ref_valid) begin

                    width_ref <= qrs_eval_width_reg;

                    width_ref_valid <= 1'b1;

                end else if (qrs_eval_width_reg >= width_ref) begin

                    width_ref <= width_ref + ((qrs_eval_width_reg - width_ref) >> REF_SHIFT);

                end else begin

                    width_ref <= width_ref - ((width_ref - qrs_eval_width_reg) >> REF_SHIFT);

                end

                if (!energy_ref_valid) begin

                    energy_ref <= qrs_eval_energy_reg;

                    energy_ref_valid <= 1'b1;

                end else if (qrs_eval_energy_reg >= energy_ref) begin

                    energy_ref <= energy_ref + ((qrs_eval_energy_reg - energy_ref) >> REF_SHIFT);

                end else begin

                    energy_ref <= energy_ref - ((energy_ref - qrs_eval_energy_reg) >> REF_SHIFT);

                end

            end

            if (qrs_eval_cond_pending) begin

                qrs_eval_cond_pending <= 1'b0;

                qrs_eval_pending <= 1'b1;

                qrs_eval_wide_reg <= (qrs_eval_width_reg >= WIDTH_TH_U) ||
                                     (qrs_eval_width_ref_valid_reg &&
                                      (qrs_eval_width_diff_abs >= WIDTH_DEV_TH_U));

                qrs_eval_complex_cond_reg <= (qrs_eval_complex_reg >= COMPLEX_TH_U);

                qrs_eval_energy_cond_reg <= qrs_eval_energy_ref_valid_reg &&
                                            (qrs_eval_energy_diff_abs >= ENERGY_DEV_TH_U);

            end



            if (clear) begin

                pre_strong_sr <= {PRE_WIN{1'b0}};

                pre_flip_sr <= {PRE_WIN{1'b0}};

                pre_strong_count <= 8'd0;

                pre_flip_count <= 8'd0;

                pre_energy_sum <= 16'd0;

                pre_strong_head <= 8'd0;

                pre_strong_tail <= 8'd0;

                pre_sample_idx <= 8'd0;

                pre_oldest_time <= 8'd0;

                pre_newest_time <= 8'd0;

                for (i = 0; i < PRE_WIN; i = i + 1)

                    pre_energy_sr[i] <= 8'd0;

                window_active <= 1'b0;

                post_count <= {WIN_WIDTH{1'b0}};

                event_seen <= 1'b0;

                first_pos <= 8'd0;

                last_pos <= 8'd0;

                event_count <= 8'd0;

                flip_count <= 8'd0;

                energy_sum <= 16'd0;

                pre_strong_at_beat <= 8'd0;

                pre_flip_at_beat <= 8'd0;

                pre_energy_at_beat <= 16'd0;

                width_ref <= 8'd0;

                energy_ref <= {CODE_WIDTH{1'b0}};

                width_ref_valid <= 1'b0;

                energy_ref_valid <= 1'b0;

                qrs_width_value <= 8'd0;

                qrs_complex_count <= {CODE_WIDTH{1'b0}};

                qrs_energy_code <= {CODE_WIDTH{1'b0}};

                qrs_eval_pending <= 1'b0;

                qrs_eval_cond_pending <= 1'b0;

                qrs_eval_width_reg <= 8'd0;

                qrs_eval_complex_reg <= {CODE_WIDTH{1'b0}};

                qrs_eval_energy_reg <= {CODE_WIDTH{1'b0}};

                qrs_eval_width_ref_reg <= 8'd0;

                qrs_eval_width_ref_valid_reg <= 1'b0;

                qrs_eval_energy_ref_reg <= {CODE_WIDTH{1'b0}};

                qrs_eval_energy_ref_valid_reg <= 1'b0;

                qrs_eval_wide_reg <= 1'b0;

                qrs_eval_complex_cond_reg <= 1'b0;

                qrs_eval_energy_cond_reg <= 1'b0;

                qrs_eval_pre_bump_reg <= 1'b0;

            end else if (sample_valid) begin

                pre_strong_sr <= {pre_strong_sr[PRE_WIN-2:0], strong_event};

                pre_flip_sr <= {pre_flip_sr[PRE_WIN-2:0], dscr_sign_flip_spike};

                pre_strong_count <= pre_strong_count_next_comb;

                pre_flip_count <= pre_flip_count + {7'd0, dscr_sign_flip_spike} - {7'd0, pre_flip_sr[PRE_WIN-1]};

                pre_energy_sum <= pre_energy_sum + {8'd0, energy_sample_code} - {8'd0, pre_energy_sr[PRE_WIN-1]};

                if (pre_strong_pop_comb)

                    pre_strong_head <= pre_strong_head_next_comb;

                if (strong_event) begin

                    pre_strong_time_fifo[pre_strong_tail] <= pre_sample_idx;

                    pre_strong_tail <= pre_strong_tail_next_comb;

                end

                pre_sample_idx <= pre_sample_idx + 8'd1;

                pre_oldest_time <= pre_oldest_time_next_comb;

                pre_newest_time <= pre_newest_time_next_comb;

                for (i = PRE_WIN-1; i > 0; i = i - 1)

                    pre_energy_sr[i] <= pre_energy_sr[i-1];

                pre_energy_sr[0] <= energy_sample_code;



                if (beat_spike) begin

                    window_active <= 1'b1;

                    post_count <= 8'd1;

                    event_seen <= pre_seen_comb || strong_event;

                    first_pos <= pre_seen_comb ? pre_first_comb : (strong_event ? PRE_WIN_U : 8'd0);

                    last_pos <= strong_event ? PRE_WIN_U : (pre_seen_comb ? pre_last_comb : 8'd0);

                    event_count <= pre_strong_count + {7'd0, strong_event};

                    flip_count <= pre_flip_count + {7'd0, dscr_sign_flip_spike};

                    energy_sum <= pre_energy_sum + {8'd0, energy_sample_code};

                    pre_strong_at_beat <= pre_strong_count;

                    pre_flip_at_beat <= pre_flip_count;

                    pre_energy_at_beat <= pre_energy_sum;

                end else if (window_active) begin

                    if (strong_event) begin

                        if (!event_seen) begin

                            event_seen <= 1'b1;

                            first_pos <= PRE_WIN_U + post_count;

                        end

                        last_pos <= PRE_WIN_U + post_count;

                        if (event_count != 8'hff)

                            event_count <= event_count + 1'b1;

                    end

                    if (dscr_sign_flip_spike && (flip_count != 8'hff))

                        flip_count <= flip_count + 1'b1;

                    energy_sum <= energy_sum_eval;



                    if (post_count >= (POST_WIN_U - 1'b1)) begin

                        window_active <= 1'b0;

                        qrs_eval_cond_pending <= 1'b1;

                        qrs_eval_width_reg <= width_eval;

                        qrs_eval_complex_reg <= complex_next;

                        qrs_eval_energy_reg <= energy_code_next;

                        qrs_eval_width_ref_reg <= width_ref;

                        qrs_eval_width_ref_valid_reg <= width_ref_valid;

                        qrs_eval_energy_ref_reg <= energy_ref;

                        qrs_eval_energy_ref_valid_reg <= energy_ref_valid;

                        qrs_eval_pre_bump_reg <= (pre_strong_at_beat != 8'd0) ||
                                                 (pre_flip_at_beat >= 8'd2) ||
                                                 (pre_energy_at_beat >= 16'd32);


                    end else begin

                        post_count <= post_count + 1'b1;

                    end

                end

            end

        end

    end



endmodule
