`timescale 1ns / 1ps

// SNN-style 30-minute final membrane layer for Snapshot V2.
//
// Structure:
//   60s snapshot pred spike -> pred_count_* membranes
//   60s feature evidence -> auxiliary evidence-neuron membranes
//   comparator gates -> excitatory/inhibitory signed stimuli into class membranes
//   final WTA -> 30-minute chunk class
//
// Candidate frozen as internal engineering baseline:
//   arr_focus_0042452 + margin_evidence_0038974
module final_membrane_layer(
    input clk,
    input rst,
    input clear,
    input snapshot_done,
    input chunk_done,
    input pred_valid,
    input [1:0] pred_class,
    input signed [63:0] class_mem_nsr,
    input signed [63:0] class_mem_chf,
    input signed [63:0] class_mem_arr,
    input signed [63:0] class_mem_aff,
    input [31:0] beat_count,
    input [31:0] pnn_mismatch_count,
    input [31:0] ectopic_pair_count,
    input [31:0] rdm_ge50_count,
    input [31:0] rdm_ge100_count,
    input [31:0] qrs_maf_count,
    input [31:0] qrs_width_abn_count,
    input [31:0] qrs_energy_abn_count,
    input [31:0] rbbb_delay_like_count,
    input [31:0] rbbb_delay_applied_count,
    input [31:0] pre_qrs_bump_count,
    input [31:0] dscr_flip_count,
    input [31:0] dscr_slope_count,
    input [31:0] abnormal_evidence_count,
    input [31:0] rhythm_irregular_evidence_count,
    input [31:0] morphology_evidence_count,
    input [31:0] pnn_decision_count,
    input [31:0] rdm_valid_count,
    input [31:0] rdm_code_sum,
    input [31:0] ram_code_sum,
    input [31:0] ram_code_count,
    output reg final_valid,
    output reg [1:0] final_pred_class,
    output reg signed [31:0] final_mem_nsr,
    output reg signed [31:0] final_mem_chf,
    output reg signed [31:0] final_mem_arr,
    output reg signed [31:0] final_mem_aff
);

    localparam [1:0] CLS_NSR = 2'd0;
    localparam [1:0] CLS_CHF = 2'd1;
    localparam [1:0] CLS_ARR = 2'd2;
    localparam [1:0] CLS_AFF = 2'd3;

    localparam [3:0] FM_IDLE      = 4'd0;
    localparam [3:0] FM_BASE      = 4'd1;
    localparam [3:0] FM_LOCAL     = 4'd2;
    localparam [3:0] FM_LOCAL_WTA = 4'd3;
    localparam [3:0] FM_POST      = 4'd4;
    localparam [3:0] FM_POST_PAIR = 4'd5;
    localparam [3:0] FM_POST_WTA  = 4'd6;
    localparam [3:0] FM_FINAL     = 4'd7;
    localparam [3:0] FM_FINAL_WTA = 4'd8;

    reg [5:0] pred_count_nsr;
    reg [5:0] pred_count_chf;
    reg [5:0] pred_count_arr;
    reg [5:0] pred_count_aff;

    reg [31:0] sum_pnn_mismatch;
    reg [31:0] sum_ectopic_pair;
    reg [31:0] sum_qrs_maf;
    reg [31:0] sum_rbbb_like;
    reg [31:0] sum_pre_qrs;
    reg [31:0] sum_abnormal;
    reg [31:0] sum_rhythm;
    reg [31:0] sum_morphology;
    reg [31:0] sum_rdm_valid;
    reg [31:0] sum_rdm_code;

    reg [3:0] final_pipe_stage;
    reg final_pipe_chunk;

    reg [5:0] dec_count_nsr;
    reg [5:0] dec_count_chf;
    reg [5:0] dec_count_arr;
    reg [5:0] dec_count_aff;
    reg [31:0] dec_pnn_mismatch;
    reg [31:0] dec_ectopic_pair;
    reg [31:0] dec_qrs_maf;
    reg [31:0] dec_rbbb_like;
    reg [31:0] dec_pre_qrs;
    reg [31:0] dec_abnormal;
    reg [31:0] dec_rhythm;
    reg [31:0] dec_morphology;
    reg [31:0] dec_rdm_valid;
    reg [31:0] dec_rdm_code;

    wire [5:0] count_nsr_next = pred_count_nsr + ((pred_valid && (pred_class == CLS_NSR)) ? 6'd1 : 6'd0);
    wire [5:0] count_chf_next = pred_count_chf + ((pred_valid && (pred_class == CLS_CHF)) ? 6'd1 : 6'd0);
    wire [5:0] count_arr_next = pred_count_arr + ((pred_valid && (pred_class == CLS_ARR)) ? 6'd1 : 6'd0);
    wire [5:0] count_aff_next = pred_count_aff + ((pred_valid && (pred_class == CLS_AFF)) ? 6'd1 : 6'd0);

    wire [31:0] pnn_mismatch_next = sum_pnn_mismatch + pnn_mismatch_count;
    wire [31:0] ectopic_pair_next = sum_ectopic_pair + ectopic_pair_count;
    wire [31:0] qrs_maf_next = sum_qrs_maf + qrs_maf_count;
    wire [31:0] rbbb_like_next = sum_rbbb_like + rbbb_delay_like_count;
    wire [31:0] pre_qrs_next = sum_pre_qrs + pre_qrs_bump_count;
    wire [31:0] abnormal_next = sum_abnormal + abnormal_evidence_count;
    wire [31:0] rhythm_next = sum_rhythm + rhythm_irregular_evidence_count;
    wire [31:0] morphology_next = sum_morphology + morphology_evidence_count;
    wire [31:0] rdm_valid_next = sum_rdm_valid + rdm_valid_count;
    wire [31:0] rdm_code_next = sum_rdm_code + rdm_code_sum;

    function [1:0] argmax_count4;
        input [5:0] a;
        input [5:0] b;
        input [5:0] c;
        input [5:0] d;
        reg [5:0] best;
        begin
            argmax_count4 = CLS_NSR;
            best = a;
            if (b > best) begin best = b; argmax_count4 = CLS_CHF; end
            if (c > best) begin best = c; argmax_count4 = CLS_ARR; end
            if (d > best) begin best = d; argmax_count4 = CLS_AFF; end
        end
    endfunction

    function [1:0] argmax_score4;
        input signed [31:0] a;
        input signed [31:0] b;
        input signed [31:0] c;
        input signed [31:0] d;
        reg signed [31:0] best;
        begin
            argmax_score4 = CLS_NSR;
            best = a;
            if (b > best) begin best = b; argmax_score4 = CLS_CHF; end
            if (c > best) begin best = c; argmax_score4 = CLS_ARR; end
            if (d > best) begin best = d; argmax_score4 = CLS_AFF; end
        end
    endfunction

    function signed [31:0] margin_score4;
        input signed [31:0] a;
        input signed [31:0] b;
        input signed [31:0] c;
        input signed [31:0] d;
        reg signed [31:0] best;
        reg signed [31:0] second;
        begin
            best = a;
            second = -32'sd2147483647;
            if (b > best) begin second = best; best = b; end else if (b > second) begin second = b; end
            if (c > best) begin second = best; best = c; end else if (c > second) begin second = c; end
            if (d > best) begin second = best; best = d; end else if (d > second) begin second = d; end
            margin_score4 = best - second;
        end
    endfunction

    reg [1:0] s1_base_pred;
    reg signed [31:0] s1_nsr_arr_margin;
    reg signed [31:0] s1_chf_aff_margin;
    reg signed [31:0] s1_arr_aff_margin;
    reg signed [31:0] s1_base_nsr;
    reg signed [31:0] s1_base_chf;
    reg signed [31:0] s1_base_arr;
    reg signed [31:0] s1_base_aff;
    reg [35:0] s1_rdm_code_ext;
    reg [35:0] s1_rdm_valid_times10;

    reg [1:0] p1_base_pred;
    reg signed [31:0] p1_nsr_arr_margin;
    reg signed [31:0] p1_chf_aff_margin;
    reg signed [31:0] p1_arr_aff_margin;
    reg signed [31:0] p1_base_nsr;
    reg signed [31:0] p1_base_chf;
    reg signed [31:0] p1_base_arr;
    reg signed [31:0] p1_base_aff;
    reg [35:0] p1_rdm_code_ext;
    reg [35:0] p1_rdm_valid_times10;

    reg signed [31:0] s2_local_nsr;
    reg signed [31:0] s2_local_chf;
    reg signed [31:0] s2_local_arr;
    reg signed [31:0] s2_local_aff;
    reg [1:0] s2_local_wta_pred;
    reg s2_aff_low_rescue;
    reg s2_nsr_from_chf_rescue;
    reg s2_chf_from_aff_rescue;
    reg s2_strong_chf;
    reg s2_arr_rescue;
    reg s2_arr_over_aff;
    reg s2_aff_rescue;
    reg s2_arr_low_rescue;
    reg s2_arr_silent_rescue;

    reg signed [31:0] p2_local_nsr;
    reg signed [31:0] p2_local_chf;
    reg signed [31:0] p2_local_arr;
    reg signed [31:0] p2_local_aff;
    reg [1:0] p2_local_pred;

    reg signed [31:0] s3_post_nsr;
    reg signed [31:0] s3_post_chf;
    reg signed [31:0] s3_post_arr;
    reg signed [31:0] s3_post_aff;
    reg [1:0] s3_arr_focus_pred;
    reg signed [31:0] s3_arr_focus_margin;
    reg s3_arr_from_nsr;
    reg s3_arr_from_chf;
    reg s3_arr_from_aff;
    reg signed [31:0] s3_nsr_chf_best_score;
    reg signed [31:0] s3_nsr_chf_second_score;
    reg signed [31:0] s3_arr_aff_best_score;
    reg signed [31:0] s3_arr_aff_second_score;
    reg [1:0] s3_nsr_chf_best_class;
    reg [1:0] s3_arr_aff_best_class;

    reg signed [31:0] p3_post_nsr;
    reg signed [31:0] p3_post_chf;
    reg signed [31:0] p3_post_arr;
    reg signed [31:0] p3_post_aff;
    reg signed [31:0] p3_nsr_chf_best_score;
    reg signed [31:0] p3_nsr_chf_second_score;
    reg signed [31:0] p3_arr_aff_best_score;
    reg signed [31:0] p3_arr_aff_second_score;
    reg [1:0] p3_nsr_chf_best_class;
    reg [1:0] p3_arr_aff_best_class;
    reg [1:0] p3_arr_focus_pred;
    reg signed [31:0] p3_arr_focus_margin;

    reg signed [31:0] s4_calc_nsr;
    reg signed [31:0] s4_calc_chf;
    reg signed [31:0] s4_calc_arr;
    reg signed [31:0] s4_calc_aff;
    reg [1:0] s4_final_pred_calc;
    reg s4_margin_evidence_rescue;
    reg signed [31:0] p4_final_nsr;
    reg signed [31:0] p4_final_chf;
    reg signed [31:0] p4_final_arr;
    reg signed [31:0] p4_final_aff;

    always @(*) begin
        s1_base_pred = argmax_count4(dec_count_nsr, dec_count_chf, dec_count_arr, dec_count_aff);
        s1_nsr_arr_margin = $signed({26'd0, dec_count_nsr}) - $signed({26'd0, dec_count_arr});
        s1_chf_aff_margin = $signed({26'd0, dec_count_chf}) - $signed({26'd0, dec_count_aff});
        s1_arr_aff_margin = $signed({26'd0, dec_count_arr}) - $signed({26'd0, dec_count_aff});

        s1_base_nsr = $signed({26'd0, dec_count_nsr}) + 32'sd2;
        s1_base_chf = $signed({26'd0, dec_count_chf});
        s1_base_arr = $signed({26'd0, dec_count_arr});
        s1_base_aff = $signed({26'd0, dec_count_aff});

        s1_rdm_code_ext = {4'd0, dec_rdm_code};
        s1_rdm_valid_times10 = ({4'd0, dec_rdm_valid} << 3) + ({4'd0, dec_rdm_valid} << 1);
    end

    always @(*) begin
        s2_local_nsr = p1_base_nsr;
        s2_local_chf = p1_base_chf;
        s2_local_arr = p1_base_arr;
        s2_local_aff = p1_base_aff;

        s2_aff_low_rescue = (p1_base_pred == CLS_CHF) &&
                            (dec_abnormal <= 32'd50) &&
                            (dec_morphology <= 32'd20) &&
                            (dec_rbbb_like <= 32'd0) &&
                            (((dec_rdm_valid > 32'd0) && (p1_rdm_code_ext >= p1_rdm_valid_times10)) ||
                             ((dec_rdm_valid == 32'd0) && (dec_rdm_code == 32'd0) &&
                              (dec_rhythm <= 32'd256) && (dec_qrs_maf <= 32'd8) && (dec_pre_qrs <= 32'd8))) &&
                            (dec_count_chf >= 6'd18);
        if (s2_aff_low_rescue) begin
            s2_local_aff = s2_local_aff + 32'sd60;
            s2_local_chf = s2_local_chf - 32'sd20;
        end

        s2_nsr_from_chf_rescue = (p1_base_pred == CLS_CHF) &&
                                 (dec_count_nsr >= 6'd3) &&
                                 (dec_abnormal <= 32'd150) &&
                                 (dec_qrs_maf <= 32'd64) &&
                                 (dec_rbbb_like <= 32'd1) &&
                                 (dec_morphology <= 32'd1500);
        if (s2_nsr_from_chf_rescue) begin
            s2_local_nsr = s2_local_nsr + 32'sd10;
            s2_local_chf = s2_local_chf - 32'sd30;
        end

        s2_chf_from_aff_rescue = (p1_base_pred == CLS_AFF) &&
                                 (dec_count_chf >= 6'd5) &&
                                 (dec_morphology <= 32'd100) &&
                                 (dec_qrs_maf <= 32'd32) &&
                                 (dec_rbbb_like <= 32'd2);
        if (s2_chf_from_aff_rescue) begin
            s2_local_chf = s2_local_chf + 32'sd20;
            s2_local_aff = s2_local_aff - 32'sd10;
        end

        s2_strong_chf = (p1_base_pred == CLS_CHF) &&
                        ((dec_count_chf >= 6'd30) || (p1_chf_aff_margin >= 32'sd24));

        s2_arr_rescue = ((p1_base_pred == CLS_NSR) || (p1_base_pred == CLS_CHF) || (p1_base_pred == CLS_AFF)) &&
                        (dec_count_arr >= 6'd12) &&
                        (dec_count_aff <= 6'd10) &&
                        (p1_nsr_arr_margin <= 32'sd24) &&
                        (dec_morphology >= 32'd180) &&
                        (dec_qrs_maf >= 32'd40) &&
                        (dec_rbbb_like >= 32'd8) &&
                        (dec_pre_qrs >= 32'd1800);
        if (s2_arr_rescue) begin
            s2_local_arr = s2_local_arr + 32'sd50;
            s2_local_nsr = s2_local_nsr - 32'sd30;
            s2_local_chf = s2_local_chf - 32'sd10;
            s2_local_aff = s2_local_aff - 32'sd5;
        end

        s2_arr_over_aff = (p1_base_pred == CLS_AFF) &&
                          (dec_count_arr >= 6'd8) &&
                          (dec_qrs_maf >= 32'd1000) &&
                          (dec_morphology >= 32'd1500);
        if (s2_arr_over_aff) begin
            s2_local_arr = s2_local_arr + 32'sd20;
            s2_local_aff = s2_local_aff - 32'sd10;
        end

        s2_aff_rescue = ((p1_base_pred == CLS_CHF) || (p1_base_pred == CLS_ARR)) &&
                        !s2_strong_chf &&
                        (dec_count_arr < 6'd15) &&
                        (dec_count_aff >= 6'd6) &&
                        (p1_chf_aff_margin <= 32'sd14) &&
                        (dec_rhythm >= 32'd1800) &&
                        (dec_ectopic_pair <= 32'd100);
        if (s2_aff_rescue) begin
            s2_local_aff = s2_local_aff + 32'sd25;
            s2_local_chf = s2_local_chf - 32'sd15;
        end

        if (s2_strong_chf) begin
            s2_local_aff = s2_local_aff - 32'sd4;
        end

        s2_arr_low_rescue = ((p1_base_pred == CLS_NSR) || (p1_base_pred == CLS_CHF) || (p1_base_pred == CLS_AFF)) &&
                            (dec_count_arr >= 6'd4) &&
                            (dec_count_aff <= 6'd3) &&
                            (dec_pre_qrs >= 32'd3000) &&
                            (dec_qrs_maf >= 32'd40) &&
                            (dec_rbbb_like >= 32'd8) &&
                            (dec_morphology >= 32'd350);
        if (s2_arr_low_rescue) begin
            s2_local_arr = s2_local_arr + 32'sd30;
            s2_local_chf = s2_local_chf - 32'sd10;
            s2_local_aff = s2_local_aff - 32'sd10;
        end

        s2_arr_silent_rescue = (p1_base_pred == CLS_NSR) &&
                               (dec_count_nsr >= 6'd18) &&
                               (dec_count_arr <= 6'd5) &&
                               (dec_abnormal >= 32'd100) &&
                               (dec_abnormal <= 32'd350) &&
                               (dec_morphology >= 32'd1500) &&
                               (dec_morphology <= 32'd6500) &&
                               (dec_qrs_maf <= 32'd20) &&
                               (dec_rbbb_like <= 32'd2) &&
                               (dec_pnn_mismatch >= 32'd32) &&
                               (dec_ectopic_pair >= 32'd8) &&
                               (dec_rdm_code >= 32'd1500) &&
                               (dec_rdm_code <= 32'd7000);
        if (s2_arr_silent_rescue) begin
            s2_local_arr = s2_local_arr + 32'sd30;
            s2_local_nsr = s2_local_nsr - 32'sd50;
        end

    end

    always @(*) begin
        s2_local_wta_pred = argmax_score4(p2_local_nsr, p2_local_chf, p2_local_arr, p2_local_aff);
    end

    always @(*) begin
        s3_post_nsr = p2_local_nsr;
        s3_post_chf = p2_local_chf;
        s3_post_arr = p2_local_arr;
        s3_post_aff = p2_local_aff;

        s3_arr_from_nsr = (p2_local_pred == CLS_NSR) &&
                          (dec_count_nsr >= 6'd18) &&
                          (dec_count_arr >= 6'd4) &&
                          (dec_count_aff <= 6'd10) &&
                          ((dec_count_nsr - dec_count_arr) <= 6'd30) &&
                          (dec_morphology >= 32'd5500) &&
                          (dec_rdm_code >= 32'd6500) &&
                          (dec_pnn_mismatch >= 32'd64) &&
                          (dec_ectopic_pair >= 32'd50) &&
                          (dec_qrs_maf <= 32'd256) &&
                          (dec_rbbb_like <= 32'd32);
        if (s3_arr_from_nsr) begin
            s3_post_arr = s3_post_arr + 32'sd16;
            s3_post_nsr = s3_post_nsr - 32'sd12;
            s3_post_aff = s3_post_aff - 32'sd4;
        end

        s3_arr_from_chf = (p2_local_pred == CLS_CHF) &&
                          (dec_count_arr >= 6'd9) &&
                          (($signed({26'd0, dec_count_chf}) - $signed({26'd0, dec_count_arr})) <= 32'sd15) &&
                          (dec_morphology >= 32'd650) &&
                          (dec_qrs_maf >= 32'd64) &&
                          (dec_rbbb_like >= 32'd12) &&
                          (dec_rdm_code >= 32'd9500) &&
                          (dec_ectopic_pair >= 32'd64);
        if (s3_arr_from_chf) begin
            s3_post_arr = s3_post_arr + 32'sd32;
            s3_post_chf = s3_post_chf - 32'sd20;
        end

        s3_arr_from_aff = (p2_local_pred == CLS_AFF) &&
                          (dec_count_arr >= 6'd5) &&
                          (($signed({26'd0, dec_count_aff}) - $signed({26'd0, dec_count_arr})) <= 32'sd20) &&
                          (dec_morphology >= 32'd1000) &&
                          (dec_rdm_code >= 32'd20000) &&
                          (dec_pnn_mismatch >= 32'd256) &&
                          (dec_ectopic_pair >= 32'd64) &&
                          (dec_qrs_maf <= 32'd512) &&
                          (dec_rbbb_like <= 32'd10);
        if (s3_arr_from_aff) begin
            s3_post_arr = s3_post_arr + 32'sd24;
            s3_post_aff = s3_post_aff - 32'sd8;
        end

    end

    always @(*) begin
        if (p3_post_chf > p3_post_nsr) begin
            s3_nsr_chf_best_score = p3_post_chf;
            s3_nsr_chf_second_score = p3_post_nsr;
            s3_nsr_chf_best_class = CLS_CHF;
        end else begin
            s3_nsr_chf_best_score = p3_post_nsr;
            s3_nsr_chf_second_score = p3_post_chf;
            s3_nsr_chf_best_class = CLS_NSR;
        end

        if (p3_post_aff > p3_post_arr) begin
            s3_arr_aff_best_score = p3_post_aff;
            s3_arr_aff_second_score = p3_post_arr;
            s3_arr_aff_best_class = CLS_AFF;
        end else begin
            s3_arr_aff_best_score = p3_post_arr;
            s3_arr_aff_second_score = p3_post_aff;
            s3_arr_aff_best_class = CLS_ARR;
        end
    end

    always @(*) begin
        if (p3_arr_aff_best_score > p3_nsr_chf_best_score) begin
            s3_arr_focus_pred = p3_arr_aff_best_class;
            if (p3_nsr_chf_best_score > p3_arr_aff_second_score)
                s3_arr_focus_margin = p3_arr_aff_best_score - p3_nsr_chf_best_score;
            else
                s3_arr_focus_margin = p3_arr_aff_best_score - p3_arr_aff_second_score;
        end else begin
            s3_arr_focus_pred = p3_nsr_chf_best_class;
            if (p3_arr_aff_best_score > p3_nsr_chf_second_score)
                s3_arr_focus_margin = p3_nsr_chf_best_score - p3_arr_aff_best_score;
            else
                s3_arr_focus_margin = p3_nsr_chf_best_score - p3_nsr_chf_second_score;
        end
    end

    always @(*) begin
        s4_calc_nsr = p3_post_nsr;
        s4_calc_chf = p3_post_chf;
        s4_calc_arr = p3_post_arr;
        s4_calc_aff = p3_post_aff;

        s4_margin_evidence_rescue = (p3_arr_focus_pred == CLS_AFF) &&
                                    (p3_arr_focus_margin <= 32'sd12) &&
                                    (dec_count_arr >= 6'd3) &&
                                    (dec_rdm_code >= 32'd512) &&
                                    (dec_pnn_mismatch >= 32'd800) &&
                                    (dec_ectopic_pair >= 32'd256) &&
                                    (dec_abnormal >= 32'd256);
        if (s4_margin_evidence_rescue) begin
            s4_calc_arr = s4_calc_arr + 32'sd4;
            s4_calc_aff = s4_calc_aff - 32'sd16;
        end
    end

    always @(*) begin
        s4_final_pred_calc = argmax_score4(p4_final_nsr, p4_final_chf, p4_final_arr, p4_final_aff);
    end

    always @(posedge clk) begin
        if (rst || clear) begin
            pred_count_nsr <= 6'd0;
            pred_count_chf <= 6'd0;
            pred_count_arr <= 6'd0;
            pred_count_aff <= 6'd0;
            sum_pnn_mismatch <= 32'd0;
            sum_ectopic_pair <= 32'd0;
            sum_qrs_maf <= 32'd0;
            sum_rbbb_like <= 32'd0;
            sum_pre_qrs <= 32'd0;
            sum_abnormal <= 32'd0;
            sum_rhythm <= 32'd0;
            sum_morphology <= 32'd0;
            sum_rdm_valid <= 32'd0;
            sum_rdm_code <= 32'd0;
            final_valid <= 1'b0;
            final_pred_class <= CLS_NSR;
            final_mem_nsr <= 32'sd0;
            final_mem_chf <= 32'sd0;
            final_mem_arr <= 32'sd0;
            final_mem_aff <= 32'sd0;
            p3_nsr_chf_best_score <= 32'sd0;
            p3_nsr_chf_second_score <= 32'sd0;
            p3_arr_aff_best_score <= 32'sd0;
            p3_arr_aff_second_score <= 32'sd0;
            p3_nsr_chf_best_class <= CLS_NSR;
            p3_arr_aff_best_class <= CLS_ARR;
            p3_arr_focus_pred <= CLS_NSR;
            p3_arr_focus_margin <= 32'sd0;
            p4_final_nsr <= 32'sd0;
            p4_final_chf <= 32'sd0;
            p4_final_arr <= 32'sd0;
            p4_final_aff <= 32'sd0;
            final_pipe_stage <= FM_IDLE;
            final_pipe_chunk <= 1'b0;
        end else begin
            final_valid <= 1'b0;
            if (snapshot_done) begin
                pred_count_nsr <= count_nsr_next;
                pred_count_chf <= count_chf_next;
                pred_count_arr <= count_arr_next;
                pred_count_aff <= count_aff_next;
                sum_pnn_mismatch <= pnn_mismatch_next;
                sum_ectopic_pair <= ectopic_pair_next;
                sum_qrs_maf <= qrs_maf_next;
                sum_rbbb_like <= rbbb_like_next;
                sum_pre_qrs <= pre_qrs_next;
                sum_abnormal <= abnormal_next;
                sum_rhythm <= rhythm_next;
                sum_morphology <= morphology_next;
                sum_rdm_valid <= rdm_valid_next;
                sum_rdm_code <= rdm_code_next;
                dec_count_nsr <= count_nsr_next;
                dec_count_chf <= count_chf_next;
                dec_count_arr <= count_arr_next;
                dec_count_aff <= count_aff_next;
                dec_pnn_mismatch <= pnn_mismatch_next;
                dec_ectopic_pair <= ectopic_pair_next;
                dec_qrs_maf <= qrs_maf_next;
                dec_rbbb_like <= rbbb_like_next;
                dec_pre_qrs <= pre_qrs_next;
                dec_abnormal <= abnormal_next;
                dec_rhythm <= rhythm_next;
                dec_morphology <= morphology_next;
                dec_rdm_valid <= rdm_valid_next;
                dec_rdm_code <= rdm_code_next;
                final_pipe_stage <= FM_BASE;
                final_pipe_chunk <= chunk_done;
            end else begin
                case (final_pipe_stage)
                    FM_BASE: begin
                        p1_base_pred <= s1_base_pred;
                        p1_nsr_arr_margin <= s1_nsr_arr_margin;
                        p1_chf_aff_margin <= s1_chf_aff_margin;
                        p1_arr_aff_margin <= s1_arr_aff_margin;
                        p1_base_nsr <= s1_base_nsr;
                        p1_base_chf <= s1_base_chf;
                        p1_base_arr <= s1_base_arr;
                        p1_base_aff <= s1_base_aff;
                        p1_rdm_code_ext <= s1_rdm_code_ext;
                        p1_rdm_valid_times10 <= s1_rdm_valid_times10;
                        final_pipe_stage <= FM_LOCAL;
                    end

                    FM_LOCAL: begin
                        p2_local_nsr <= s2_local_nsr;
                        p2_local_chf <= s2_local_chf;
                        p2_local_arr <= s2_local_arr;
                        p2_local_aff <= s2_local_aff;
                        final_pipe_stage <= FM_LOCAL_WTA;
                    end

                    FM_LOCAL_WTA: begin
                        p2_local_pred <= s2_local_wta_pred;
                        final_pipe_stage <= FM_POST;
                    end

                    FM_POST: begin
                        p3_post_nsr <= s3_post_nsr;
                        p3_post_chf <= s3_post_chf;
                        p3_post_arr <= s3_post_arr;
                        p3_post_aff <= s3_post_aff;
                        final_pipe_stage <= FM_POST_PAIR;
                    end

                    FM_POST_PAIR: begin
                        p3_nsr_chf_best_score <= s3_nsr_chf_best_score;
                        p3_nsr_chf_second_score <= s3_nsr_chf_second_score;
                        p3_arr_aff_best_score <= s3_arr_aff_best_score;
                        p3_arr_aff_second_score <= s3_arr_aff_second_score;
                        p3_nsr_chf_best_class <= s3_nsr_chf_best_class;
                        p3_arr_aff_best_class <= s3_arr_aff_best_class;
                        final_pipe_stage <= FM_POST_WTA;
                    end

                    FM_POST_WTA: begin
                        p3_arr_focus_pred <= s3_arr_focus_pred;
                        p3_arr_focus_margin <= s3_arr_focus_margin;
                        final_pipe_stage <= FM_FINAL;
                    end

                    FM_FINAL: begin
                        p4_final_nsr <= s4_calc_nsr;
                        p4_final_chf <= s4_calc_chf;
                        p4_final_arr <= s4_calc_arr;
                        p4_final_aff <= s4_calc_aff;
                        final_pipe_stage <= FM_FINAL_WTA;
                    end

                    FM_FINAL_WTA: begin
                        final_mem_nsr <= p4_final_nsr;
                        final_mem_chf <= p4_final_chf;
                        final_mem_arr <= p4_final_arr;
                        final_mem_aff <= p4_final_aff;
                        final_pred_class <= s4_final_pred_calc;
                        final_valid <= final_pipe_chunk;
                        final_pipe_chunk <= 1'b0;
                        final_pipe_stage <= FM_IDLE;
                    end

                    default: begin
                        final_pipe_chunk <= 1'b0;
                        final_pipe_stage <= FM_IDLE;
                    end
                endcase
            end
        end
    end

endmodule
