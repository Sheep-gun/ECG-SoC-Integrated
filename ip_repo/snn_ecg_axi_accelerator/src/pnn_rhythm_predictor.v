`timescale 1ns / 1ps

module pnn_rhythm_predictor #(
    parameter NUM_HYP     = 46,
    parameter ID_WIDTH    = 6,
    parameter AGE_WIDTH   = 12,
    parameter BASE_DELAY  = 250,
    parameter DELAY_STEP  = 50,
    parameter WINDOW_HALF = 125
)(
    input clk,
    input rst,
    input clear,
    input rhythm_tick,
    input beat_spike,
    output reg token_active,
    output reg [AGE_WIDTH-1:0] token_age,
    output reg [AGE_WIDTH-1:0] rr_interval,
    output reg [ID_WIDTH-1:0] winner_id,
    output reg [ID_WIDTH-1:0] predictor_id,
    output reg [AGE_WIDTH-1:0] predictor_center,
    output reg winner_valid,
    output reg predictor_valid,
    output reg [AGE_WIDTH-1:0] winner_error,
    output reg [AGE_WIDTH-1:0] predictor_error,
    output reg pnn_match_spike,
    output reg pnn_mismatch_spike
);

    reg evaluating;
    reg [ID_WIDTH-1:0] eval_idx;
    reg [AGE_WIDTH-1:0] eval_age;
    reg [ID_WIDTH-1:0] eval_best_id;
    reg [AGE_WIDTH-1:0] eval_best_err;
    reg [ID_WIDTH-1:0] eval_predictor_id;
    reg eval_predictor_valid;

    wire [AGE_WIDTH-1:0] age_eval;
    wire [AGE_WIDTH-1:0] scan_center;
    wire [AGE_WIDTH-1:0] scan_err;
    wire scan_better;
    wire [ID_WIDTH-1:0] scan_best_id_next;
    wire [AGE_WIDTH-1:0] scan_best_err_next;
    wire [AGE_WIDTH-1:0] predictor_err_next;
    wire match_next;

    function [AGE_WIDTH-1:0] sat_age_inc;
        input [AGE_WIDTH-1:0] value;
        begin
            if (value == {AGE_WIDTH{1'b1}})
                sat_age_inc = value;
            else
                sat_age_inc = value + 1'b1;
        end
    endfunction

    function [AGE_WIDTH-1:0] hyp_center;
        input [ID_WIDTH-1:0] idx;
        begin
            case (idx)
                0:  hyp_center = BASE_DELAY + (0  * DELAY_STEP);
                1:  hyp_center = BASE_DELAY + (1  * DELAY_STEP);
                2:  hyp_center = BASE_DELAY + (2  * DELAY_STEP);
                3:  hyp_center = BASE_DELAY + (3  * DELAY_STEP);
                4:  hyp_center = BASE_DELAY + (4  * DELAY_STEP);
                5:  hyp_center = BASE_DELAY + (5  * DELAY_STEP);
                6:  hyp_center = BASE_DELAY + (6  * DELAY_STEP);
                7:  hyp_center = BASE_DELAY + (7  * DELAY_STEP);
                8:  hyp_center = BASE_DELAY + (8  * DELAY_STEP);
                9:  hyp_center = BASE_DELAY + (9  * DELAY_STEP);
                10: hyp_center = BASE_DELAY + (10 * DELAY_STEP);
                11: hyp_center = BASE_DELAY + (11 * DELAY_STEP);
                12: hyp_center = BASE_DELAY + (12 * DELAY_STEP);
                13: hyp_center = BASE_DELAY + (13 * DELAY_STEP);
                14: hyp_center = BASE_DELAY + (14 * DELAY_STEP);
                15: hyp_center = BASE_DELAY + (15 * DELAY_STEP);
                16: hyp_center = BASE_DELAY + (16 * DELAY_STEP);
                17: hyp_center = BASE_DELAY + (17 * DELAY_STEP);
                18: hyp_center = BASE_DELAY + (18 * DELAY_STEP);
                19: hyp_center = BASE_DELAY + (19 * DELAY_STEP);
                20: hyp_center = BASE_DELAY + (20 * DELAY_STEP);
                21: hyp_center = BASE_DELAY + (21 * DELAY_STEP);
                22: hyp_center = BASE_DELAY + (22 * DELAY_STEP);
                23: hyp_center = BASE_DELAY + (23 * DELAY_STEP);
                24: hyp_center = BASE_DELAY + (24 * DELAY_STEP);
                25: hyp_center = BASE_DELAY + (25 * DELAY_STEP);
                26: hyp_center = BASE_DELAY + (26 * DELAY_STEP);
                27: hyp_center = BASE_DELAY + (27 * DELAY_STEP);
                28: hyp_center = BASE_DELAY + (28 * DELAY_STEP);
                29: hyp_center = BASE_DELAY + (29 * DELAY_STEP);
                30: hyp_center = BASE_DELAY + (30 * DELAY_STEP);
                31: hyp_center = BASE_DELAY + (31 * DELAY_STEP);
                32: hyp_center = BASE_DELAY + (32 * DELAY_STEP);
                33: hyp_center = BASE_DELAY + (33 * DELAY_STEP);
                34: hyp_center = BASE_DELAY + (34 * DELAY_STEP);
                35: hyp_center = BASE_DELAY + (35 * DELAY_STEP);
                36: hyp_center = BASE_DELAY + (36 * DELAY_STEP);
                37: hyp_center = BASE_DELAY + (37 * DELAY_STEP);
                38: hyp_center = BASE_DELAY + (38 * DELAY_STEP);
                39: hyp_center = BASE_DELAY + (39 * DELAY_STEP);
                40: hyp_center = BASE_DELAY + (40 * DELAY_STEP);
                41: hyp_center = BASE_DELAY + (41 * DELAY_STEP);
                42: hyp_center = BASE_DELAY + (42 * DELAY_STEP);
                43: hyp_center = BASE_DELAY + (43 * DELAY_STEP);
                44: hyp_center = BASE_DELAY + (44 * DELAY_STEP);
                45: hyp_center = BASE_DELAY + (45 * DELAY_STEP);
                default: hyp_center = BASE_DELAY + (45 * DELAY_STEP);
            endcase
        end
    endfunction

    function [AGE_WIDTH-1:0] abs_diff;
        input [AGE_WIDTH-1:0] a;
        input [AGE_WIDTH-1:0] b;
        begin
            if (a >= b)
                abs_diff = a - b;
            else
                abs_diff = b - a;
        end
    endfunction

    assign age_eval = (token_active && rhythm_tick) ? sat_age_inc(token_age) : token_age;
    assign scan_center = hyp_center(eval_idx);
    assign scan_err = abs_diff(eval_age, scan_center);
    assign scan_better = (scan_err < eval_best_err);
    assign scan_best_id_next = scan_better ? eval_idx : eval_best_id;
    assign scan_best_err_next = scan_better ? scan_err : eval_best_err;
    assign predictor_err_next = abs_diff(eval_age, hyp_center(eval_predictor_id));
    assign match_next = eval_predictor_valid && (predictor_err_next <= WINDOW_HALF);

    always @(posedge clk) begin
        if (rst) begin
            token_active <= 1'b0;
            token_age <= {AGE_WIDTH{1'b0}};
            rr_interval <= {AGE_WIDTH{1'b0}};
            winner_id <= {ID_WIDTH{1'b0}};
            predictor_id <= {ID_WIDTH{1'b0}};
            predictor_center <= {AGE_WIDTH{1'b0}};
            winner_valid <= 1'b0;
            predictor_valid <= 1'b0;
            winner_error <= {AGE_WIDTH{1'b1}};
            predictor_error <= {AGE_WIDTH{1'b1}};
            pnn_match_spike <= 1'b0;
            pnn_mismatch_spike <= 1'b0;
            evaluating <= 1'b0;
            eval_idx <= {ID_WIDTH{1'b0}};
            eval_age <= {AGE_WIDTH{1'b0}};
            eval_best_id <= {ID_WIDTH{1'b0}};
            eval_best_err <= {AGE_WIDTH{1'b1}};
            eval_predictor_id <= {ID_WIDTH{1'b0}};
            eval_predictor_valid <= 1'b0;
        end else begin
            pnn_match_spike <= 1'b0;
            pnn_mismatch_spike <= 1'b0;

            if (clear) begin
                token_active <= 1'b0;
                token_age <= {AGE_WIDTH{1'b0}};
                rr_interval <= {AGE_WIDTH{1'b0}};
                winner_id <= {ID_WIDTH{1'b0}};
                predictor_id <= {ID_WIDTH{1'b0}};
                predictor_center <= {AGE_WIDTH{1'b0}};
                winner_valid <= 1'b0;
                predictor_valid <= 1'b0;
                winner_error <= {AGE_WIDTH{1'b1}};
                predictor_error <= {AGE_WIDTH{1'b1}};
                pnn_match_spike <= 1'b0;
                pnn_mismatch_spike <= 1'b0;
                evaluating <= 1'b0;
                eval_idx <= {ID_WIDTH{1'b0}};
                eval_age <= {AGE_WIDTH{1'b0}};
                eval_best_id <= {ID_WIDTH{1'b0}};
                eval_best_err <= {AGE_WIDTH{1'b1}};
                eval_predictor_id <= {ID_WIDTH{1'b0}};
                eval_predictor_valid <= 1'b0;
            end else if (beat_spike) begin
                if (token_active) begin
                    rr_interval <= age_eval;
                    eval_age <= age_eval;
                    eval_idx <= {ID_WIDTH{1'b0}};
                    eval_best_id <= {ID_WIDTH{1'b0}};
                    eval_best_err <= {AGE_WIDTH{1'b1}};
                    eval_predictor_id <= predictor_id;
                    eval_predictor_valid <= predictor_valid;
                    evaluating <= 1'b1;
                end else begin
                    winner_valid <= 1'b0;
                    predictor_valid <= 1'b0;
                    predictor_error <= {AGE_WIDTH{1'b1}};
                    evaluating <= 1'b0;
                end

                token_active <= 1'b1;
                token_age <= {AGE_WIDTH{1'b0}};
            end else begin
                if (rhythm_tick) begin
                    if (evaluating) begin
                        if (eval_idx == (NUM_HYP - 1)) begin
                            winner_id <= scan_best_id_next;
                            winner_error <= scan_best_err_next;
                            winner_valid <= 1'b1;
                            predictor_id <= scan_best_id_next;
                            predictor_center <= hyp_center(scan_best_id_next);
                            predictor_valid <= 1'b1;
                            evaluating <= 1'b0;

                            if (eval_predictor_valid) begin
                                predictor_error <= predictor_err_next;
                                pnn_match_spike <= match_next;
                                pnn_mismatch_spike <= !match_next;
                            end else begin
                                predictor_error <= {AGE_WIDTH{1'b1}};
                            end
                        end else begin
                            eval_best_id <= scan_best_id_next;
                            eval_best_err <= scan_best_err_next;
                            eval_idx <= eval_idx + 1'b1;
                        end
                    end

                    if (token_active)
                        token_age <= sat_age_inc(token_age);
                end
            end
        end
    end

endmodule
