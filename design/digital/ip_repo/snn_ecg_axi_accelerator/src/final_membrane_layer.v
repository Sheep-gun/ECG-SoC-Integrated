`timescale 1ns / 1ps

// Locked strict record-wise 30-minute final membrane readout.
//
// Candidate:
//   structural_guarded_silent_aff_1008710
//
// Python source of truth:
//   configs/recordwise_resplit_seed20260808/best_final_membrane_structural_grid_locked.json
//
// Structure:
//   60s snapshot class spikes and evidence counters
//   -> base SNN final membrane candidate balanced_0202881
//   -> structural guard/rescue/silent-AFF overlay
//   -> final WTA with strict ">" tie-break order NSR, CHF, ARR, AFF.
//
// The module interface is unchanged from the previous Final Membrane layer.
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

    `include "strict_recordwise_locked_params.vh"

    localparam [1:0] CLS_NSR = 2'd0;
    localparam [1:0] CLS_CHF = 2'd1;
    localparam [1:0] CLS_ARR = 2'd2;
    localparam [1:0] CLS_AFF = 2'd3;

    localparam [2:0] FM_IDLE       = 3'd0;
    localparam [2:0] FM_BASE       = 3'd1;
    localparam [2:0] FM_BASE_APPLY = 3'd2;
    localparam [2:0] FM_STRUCT     = 3'd3;
    localparam [2:0] FM_WTA        = 3'd4;

    reg [5:0] pred_count_nsr;
    reg [5:0] pred_count_chf;
    reg [5:0] pred_count_arr;
    reg [5:0] pred_count_aff;

    reg [31:0] sum_beat;
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
    reg [31:0] sum_ram_code;

    reg [2:0] final_pipe_stage;
    reg final_pipe_chunk;

    (* keep = "true", dont_touch = "true" *) reg [5:0] dec_count_nsr;
    (* keep = "true", dont_touch = "true" *) reg [5:0] dec_count_chf;
    (* keep = "true", dont_touch = "true" *) reg [5:0] dec_count_arr;
    (* keep = "true", dont_touch = "true" *) reg [5:0] dec_count_aff;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_beat;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_pnn_mismatch;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_ectopic_pair;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_qrs_maf;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_rbbb_like;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_pre_qrs;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_abnormal;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_rhythm;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_morphology;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_rdm_valid;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_rdm_code;
    (* keep = "true", dont_touch = "true" *) reg [31:0] dec_ram_code;

    reg signed [31:0] base_mem_nsr;
    reg signed [31:0] base_mem_chf;
    reg signed [31:0] base_mem_arr;
    reg signed [31:0] base_mem_aff;

    reg signed [31:0] base_seed_nsr;
    reg signed [31:0] base_seed_chf;
    reg signed [31:0] base_seed_arr;
    reg signed [31:0] base_seed_aff;
    reg gate_base_aff_low_r;
    reg gate_base_nsr_from_chf_r;
    reg gate_base_chf_from_aff_r;
    reg gate_base_aff_r;
    reg gate_base_arr_r;
    reg gate_base_aff_rescue_r;
    reg gate_base_arr_low_r;

    reg signed [31:0] struct_mem_nsr;
    reg signed [31:0] struct_mem_chf;
    reg signed [31:0] struct_mem_arr;
    reg signed [31:0] struct_mem_aff;

    wire [5:0] count_nsr_next = pred_count_nsr + ((pred_valid && (pred_class == CLS_NSR)) ? 6'd1 : 6'd0);
    wire [5:0] count_chf_next = pred_count_chf + ((pred_valid && (pred_class == CLS_CHF)) ? 6'd1 : 6'd0);
    wire [5:0] count_arr_next = pred_count_arr + ((pred_valid && (pred_class == CLS_ARR)) ? 6'd1 : 6'd0);
    wire [5:0] count_aff_next = pred_count_aff + ((pred_valid && (pred_class == CLS_AFF)) ? 6'd1 : 6'd0);

    wire [31:0] beat_next = sum_beat + beat_count;
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
    wire [31:0] ram_code_next = sum_ram_code + ram_code_sum;

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

    wire [1:0] base_pred_comb = argmax_count4(dec_count_nsr, dec_count_chf, dec_count_arr, dec_count_aff);
    wire base_is_nsr = (base_pred_comb == CLS_NSR);
    wire base_is_chf = (base_pred_comb == CLS_CHF);
    wire base_is_arr = (base_pred_comb == CLS_ARR);
    wire base_is_aff = (base_pred_comb == CLS_AFF);

    wire signed [31:0] dec_count_nsr_s = $signed({26'd0, dec_count_nsr});
    wire signed [31:0] dec_count_chf_s = $signed({26'd0, dec_count_chf});
    wire signed [31:0] dec_count_arr_s = $signed({26'd0, dec_count_arr});
    wire signed [31:0] dec_count_aff_s = $signed({26'd0, dec_count_aff});
    wire signed [31:0] dec_nsr_minus_arr_s = dec_count_nsr_s - dec_count_arr_s;
    wire signed [31:0] dec_chf_minus_aff_s = dec_count_chf_s - dec_count_aff_s;

    wire [39:0] rdm_valid_ext = {8'd0, dec_rdm_valid};
    wire [39:0] rdm_code_ext = {8'd0, dec_rdm_code};
    wire [39:0] rdm_threshold_11 = (rdm_valid_ext << 3) + (rdm_valid_ext << 1) + rdm_valid_ext;
    wire rdm_code_ge_base_aff_low = (dec_rdm_valid != 32'd0) && (rdm_code_ext >= rdm_threshold_11);

    wire strong_nsr =
        base_is_nsr &&
        ((dec_count_nsr >= STRICT_RW_BASE_STRONG_NSR_COUNT_GE) ||
         ((dec_nsr_minus_arr_s >= STRICT_RW_BASE_STRONG_NSR_MARGIN_GE) &&
          (dec_morphology <= STRICT_RW_BASE_STRONG_NSR_MORPH_LE) &&
          (dec_qrs_maf <= STRICT_RW_BASE_STRONG_NSR_QRS_LE)));

    wire strong_chf =
        base_is_chf &&
        ((dec_count_chf >= STRICT_RW_BASE_STRONG_CHF_COUNT_GE) ||
         (dec_chf_minus_aff_s >= STRICT_RW_BASE_STRONG_CHF_MARGIN_GE));

    wire gate_base_aff_low =
        (STRICT_RW_BASE_AFF_LOW_ENABLE != 0) &&
        base_is_chf &&
        (dec_abnormal <= STRICT_RW_BASE_AFF_LOW_ABN_LE) &&
        (dec_morphology <= STRICT_RW_BASE_AFF_LOW_MORPH_LE) &&
        (dec_rbbb_like <= STRICT_RW_BASE_AFF_LOW_RBBB_LE) &&
        rdm_code_ge_base_aff_low &&
        (dec_count_chf >= STRICT_RW_BASE_AFF_LOW_CHF_COUNT_GE);

    wire gate_base_nsr_from_chf =
        base_is_chf &&
        (dec_count_nsr >= STRICT_RW_BASE_NSR_FROM_CHF_NSR_COUNT_GE) &&
        (dec_abnormal <= STRICT_RW_BASE_NSR_FROM_CHF_ABN_LE) &&
        (dec_qrs_maf <= STRICT_RW_BASE_NSR_FROM_CHF_QRS_LE) &&
        (dec_rbbb_like <= STRICT_RW_BASE_NSR_FROM_CHF_RBBB_LE) &&
        (dec_morphology <= STRICT_RW_BASE_NSR_FROM_CHF_MORPH_LE);

    wire gate_base_chf_from_aff =
        base_is_aff &&
        (dec_count_chf >= STRICT_RW_BASE_CHF_FROM_AFF_CHF_COUNT_GE) &&
        (dec_morphology <= STRICT_RW_BASE_CHF_FROM_AFF_MORPH_LE) &&
        (dec_qrs_maf <= STRICT_RW_BASE_CHF_FROM_AFF_QRS_LE) &&
        (dec_rbbb_like <= STRICT_RW_BASE_CHF_FROM_AFF_RBBB_LE);

    wire gate_base_aff =
        (dec_count_arr < STRICT_RW_BASE_AFF_BLOCK_ARR_COUNT_GE) &&
        (base_is_chf || base_is_arr) &&
        (!strong_chf) &&
        (dec_count_aff >= STRICT_RW_BASE_AFF_COUNT_GE) &&
        (dec_chf_minus_aff_s <= STRICT_RW_BASE_AFF_CHF_MARGIN_LE) &&
        (dec_rhythm >= STRICT_RW_BASE_AFF_RHYTHM_GE) &&
        (dec_ectopic_pair >= STRICT_RW_BASE_AFF_ECP_GE) &&
        (dec_ectopic_pair <= STRICT_RW_BASE_AFF_ECP_LE);

    wire gate_base_arr =
        (!base_is_arr) &&
        (!strong_nsr) &&
        (dec_count_arr >= STRICT_RW_BASE_ARR_COUNT_GE) &&
        (dec_count_aff <= STRICT_RW_BASE_ARR_AFF_COUNT_LE) &&
        (dec_nsr_minus_arr_s <= STRICT_RW_BASE_ARR_NSR_MARGIN_LE) &&
        (dec_morphology >= STRICT_RW_BASE_ARR_MORPH_GE) &&
        (dec_qrs_maf >= STRICT_RW_BASE_ARR_QRS_GE) &&
        (dec_rbbb_like >= STRICT_RW_BASE_ARR_RBBB_GE) &&
        (dec_pre_qrs >= STRICT_RW_BASE_ARR_PRE_GE);

    wire gate_base_aff_rescue_source_ok =
        ((STRICT_RW_BASE_AFF_RESCUE_SOURCE_CHF != 0) && base_is_chf) ||
        ((STRICT_RW_BASE_AFF_RESCUE_SOURCE_ARR != 0) && base_is_arr);

    wire gate_base_aff_rescue =
        (STRICT_RW_BASE_AFF_RESCUE_ENABLE != 0) &&
        gate_base_aff_rescue_source_ok &&
        (dec_count_arr < STRICT_RW_BASE_AFF_RESCUE_ARR_COUNT_LT) &&
        (dec_count_aff >= STRICT_RW_BASE_AFF_RESCUE_COUNT_GE) &&
        (dec_chf_minus_aff_s <= STRICT_RW_BASE_AFF_RESCUE_CHF_MARGIN_LE) &&
        (dec_rhythm >= STRICT_RW_BASE_AFF_RESCUE_RHYTHM_GE) &&
        (dec_ectopic_pair >= STRICT_RW_BASE_AFF_RESCUE_ECT_GE);

    wire gate_base_arr_low =
        (STRICT_RW_BASE_ARR_LOW_ENABLE != 0) &&
        (!base_is_arr) &&
        (dec_count_arr >= STRICT_RW_BASE_ARR_LOW_COUNT_GE) &&
        (dec_count_aff <= STRICT_RW_BASE_ARR_LOW_AFF_COUNT_LE) &&
        (dec_pre_qrs >= STRICT_RW_BASE_ARR_LOW_PRE_GE) &&
        (dec_qrs_maf >= STRICT_RW_BASE_ARR_LOW_QRS_GE) &&
        (dec_rbbb_like >= STRICT_RW_BASE_ARR_LOW_RBBB_GE) &&
        (dec_morphology >= STRICT_RW_BASE_ARR_LOW_MORPH_GE) &&
        (dec_abnormal >= STRICT_RW_BASE_ARR_LOW_ABN_GE);

    wire signed [31:0] base_mem_nsr_comb =
        base_seed_nsr +
        (gate_base_nsr_from_chf_r ? STRICT_RW_BASE_NSR_FROM_CHF_BOOST : 32'sd0) -
        (gate_base_arr_r ? STRICT_RW_BASE_ARR_INHIBIT_NSR : 32'sd0) -
        (gate_base_arr_low_r ? STRICT_RW_BASE_ARR_LOW_INHIBIT_NSR : 32'sd0);

    wire signed [31:0] base_mem_chf_comb =
        base_seed_chf -
        (gate_base_aff_low_r ? STRICT_RW_BASE_AFF_LOW_INHIBIT_CHF : 32'sd0) -
        (gate_base_nsr_from_chf_r ? STRICT_RW_BASE_NSR_FROM_CHF_INHIBIT_CHF : 32'sd0) +
        (gate_base_chf_from_aff_r ? STRICT_RW_BASE_CHF_FROM_AFF_BOOST : 32'sd0) -
        (gate_base_aff_r ? STRICT_RW_BASE_AFF_INHIBIT_CHF : 32'sd0) -
        (gate_base_arr_r ? STRICT_RW_BASE_ARR_INHIBIT_CHF : 32'sd0) -
        (gate_base_aff_rescue_r ? STRICT_RW_BASE_AFF_RESCUE_INHIBIT_CHF : 32'sd0) -
        (gate_base_arr_low_r ? STRICT_RW_BASE_ARR_LOW_INHIBIT_CHF : 32'sd0);

    wire signed [31:0] base_mem_arr_comb =
        base_seed_arr -
        (gate_base_aff_r ? STRICT_RW_BASE_AFF_INHIBIT_ARR : 32'sd0) +
        (gate_base_arr_r ? STRICT_RW_BASE_ARR_BOOST : 32'sd0) -
        (gate_base_aff_rescue_r ? STRICT_RW_BASE_AFF_RESCUE_INHIBIT_ARR : 32'sd0) +
        (gate_base_arr_low_r ? STRICT_RW_BASE_ARR_LOW_BOOST : 32'sd0);

    wire signed [31:0] base_mem_aff_comb =
        base_seed_aff +
        (gate_base_aff_low_r ? STRICT_RW_BASE_AFF_LOW_BOOST : 32'sd0) -
        (gate_base_chf_from_aff_r ? STRICT_RW_BASE_CHF_FROM_AFF_INHIBIT_AFF : 32'sd0) +
        (gate_base_aff_r ? STRICT_RW_BASE_AFF_BOOST : 32'sd0) -
        (gate_base_arr_r ? STRICT_RW_BASE_ARR_INHIBIT_AFF : 32'sd0) +
        (gate_base_aff_rescue_r ? STRICT_RW_BASE_AFF_RESCUE_BOOST : 32'sd0) -
        (gate_base_arr_low_r ? STRICT_RW_BASE_ARR_LOW_INHIBIT_AFF : 32'sd0);

    wire gate_struct_aff_persistence =
        (dec_count_aff >= STRICT_RW_FINAL_AFF_CNT) &&
        (dec_count_chf >= STRICT_RW_FINAL_AFF_CHF_CNT) &&
        (dec_morphology <= STRICT_RW_FINAL_AFF_MORPH_LE) &&
        (dec_rhythm >= STRICT_RW_FINAL_AFF_RHYTHM_GE) &&
        (dec_qrs_maf <= STRICT_RW_FINAL_AFF_QRS_LE);

    wire gate_struct_nsr_clean_chf =
        (dec_count_nsr >= STRICT_RW_FINAL_NSR_CNT) &&
        (dec_count_chf >= STRICT_RW_FINAL_NSR_CHF_CNT) &&
        (dec_morphology <= STRICT_RW_FINAL_NSR_MORPH_LE) &&
        (dec_abnormal <= STRICT_RW_FINAL_NSR_ABN_LE) &&
        (dec_qrs_maf <= STRICT_RW_FINAL_NSR_QRS_LE) &&
        (dec_ectopic_pair <= STRICT_RW_FINAL_NSR_ECT_LE);

    wire gate_struct_arr_nsr_high =
        (dec_count_arr >= STRICT_RW_FINAL_ARR_NSR_ARR_CNT) &&
        (dec_qrs_maf <= STRICT_RW_FINAL_ARR_NSR_QRS_HIGH_LE) &&
        (dec_rbbb_like <= STRICT_RW_FINAL_ARR_NSR_RBBB_HIGH_LE);

    wire gate_struct_arr_nsr_low =
        (dec_count_arr <= STRICT_RW_FINAL_ARR_NSR_ARR_LOW_LE) &&
        (dec_qrs_maf <= STRICT_RW_FINAL_ARR_NSR_QRS_LOW_LE) &&
        (dec_ectopic_pair <= STRICT_RW_FINAL_ARR_NSR_ECT_LOW_LE) &&
        (dec_rhythm <= STRICT_RW_FINAL_ARR_NSR_RHYTHM_LOW_LE);

    wire gate_struct_arr_over_nsr =
        (dec_count_nsr >= STRICT_RW_FINAL_ARR_NSR_NSR_CNT) &&
        (dec_morphology >= STRICT_RW_FINAL_ARR_NSR_MORPH_GE) &&
        (dec_pre_qrs >= STRICT_RW_FINAL_ARR_NSR_PRE_GE) &&
        (gate_struct_arr_nsr_high || gate_struct_arr_nsr_low);

    wire gate_struct_arr_over_aff =
        (dec_count_aff >= STRICT_RW_FINAL_ARR_AFF_AFF_CNT) &&
        (dec_count_arr >= STRICT_RW_FINAL_ARR_AFF_ARR_CNT) &&
        (dec_morphology >= STRICT_RW_FINAL_ARR_AFF_MORPH_GE) &&
        (dec_ectopic_pair >= STRICT_RW_FINAL_ARR_AFF_ECT_GE) &&
        (dec_qrs_maf <= STRICT_RW_FINAL_ARR_AFF_QRS_LE);

    wire gate_struct_silent_aff =
        (dec_count_chf >= STRICT_RW_SILENT_AFF_CHF_CNT_GE) &&
        (dec_count_nsr <= STRICT_RW_SILENT_AFF_NSR_CNT_LE) &&
        (dec_count_arr == STRICT_RW_SILENT_AFF_ARR_CNT_EQ) &&
        (dec_count_aff == STRICT_RW_SILENT_AFF_AFF_CNT_EQ) &&
        (dec_beat <= STRICT_RW_SILENT_AFF_BEAT_LE) &&
        (dec_morphology <= STRICT_RW_SILENT_AFF_MORPH_LE) &&
        (dec_rhythm <= STRICT_RW_SILENT_AFF_RHYTHM_LE) &&
        (dec_abnormal <= STRICT_RW_SILENT_AFF_ABN_LE) &&
        (dec_qrs_maf <= STRICT_RW_SILENT_AFF_QRS_LE) &&
        (dec_ectopic_pair == STRICT_RW_SILENT_AFF_ECT_EQ) &&
        (dec_ram_code == STRICT_RW_SILENT_AFF_RAM_EQ);

    wire signed [31:0] struct_mem_nsr_comb =
        base_mem_nsr +
        (gate_struct_nsr_clean_chf ? STRICT_RW_FINAL_NSR_BOOST : 32'sd0) -
        (gate_struct_arr_over_nsr ? STRICT_RW_FINAL_ARR_NSR_INH_NSR : 32'sd0);

    wire signed [31:0] struct_mem_chf_comb =
        base_mem_chf -
        (gate_struct_aff_persistence ? STRICT_RW_FINAL_AFF_INH_CHF : 32'sd0) -
        (gate_struct_nsr_clean_chf ? STRICT_RW_FINAL_NSR_INH_CHF : 32'sd0) -
        (gate_struct_arr_over_nsr ? STRICT_RW_FINAL_ARR_NSR_INH_CHF : 32'sd0) -
        (gate_struct_silent_aff ? STRICT_RW_SILENT_AFF_INH_CHF : 32'sd0);

    wire signed [31:0] struct_mem_arr_comb =
        base_mem_arr -
        (gate_struct_aff_persistence ? STRICT_RW_FINAL_AFF_INH_ARR : 32'sd0) -
        (gate_struct_nsr_clean_chf ? STRICT_RW_FINAL_NSR_INH_ARR : 32'sd0) +
        (gate_struct_arr_over_nsr ? STRICT_RW_FINAL_ARR_NSR_BOOST : 32'sd0) +
        (gate_struct_arr_over_aff ? STRICT_RW_FINAL_ARR_AFF_BOOST : 32'sd0);

    wire signed [31:0] struct_mem_aff_comb =
        base_mem_aff +
        (gate_struct_aff_persistence ? STRICT_RW_FINAL_AFF_BOOST : 32'sd0) -
        (gate_struct_arr_over_nsr ? STRICT_RW_FINAL_ARR_NSR_INH_AFF : 32'sd0) -
        (gate_struct_arr_over_aff ? STRICT_RW_FINAL_ARR_AFF_INH_AFF : 32'sd0) +
        (gate_struct_silent_aff ? STRICT_RW_SILENT_AFF_BOOST : 32'sd0);

    always @(posedge clk) begin
        if (rst || clear) begin
            pred_count_nsr <= 6'd0;
            pred_count_chf <= 6'd0;
            pred_count_arr <= 6'd0;
            pred_count_aff <= 6'd0;
            sum_beat <= 32'd0;
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
            sum_ram_code <= 32'd0;
            final_pipe_stage <= FM_IDLE;
            final_pipe_chunk <= 1'b0;
            dec_count_nsr <= 6'd0;
            dec_count_chf <= 6'd0;
            dec_count_arr <= 6'd0;
            dec_count_aff <= 6'd0;
            dec_beat <= 32'd0;
            dec_pnn_mismatch <= 32'd0;
            dec_ectopic_pair <= 32'd0;
            dec_qrs_maf <= 32'd0;
            dec_rbbb_like <= 32'd0;
            dec_pre_qrs <= 32'd0;
            dec_abnormal <= 32'd0;
            dec_rhythm <= 32'd0;
            dec_morphology <= 32'd0;
            dec_rdm_valid <= 32'd0;
            dec_rdm_code <= 32'd0;
            dec_ram_code <= 32'd0;
            base_mem_nsr <= 32'sd0;
            base_mem_chf <= 32'sd0;
            base_mem_arr <= 32'sd0;
            base_mem_aff <= 32'sd0;
            base_seed_nsr <= 32'sd0;
            base_seed_chf <= 32'sd0;
            base_seed_arr <= 32'sd0;
            base_seed_aff <= 32'sd0;
            gate_base_aff_low_r <= 1'b0;
            gate_base_nsr_from_chf_r <= 1'b0;
            gate_base_chf_from_aff_r <= 1'b0;
            gate_base_aff_r <= 1'b0;
            gate_base_arr_r <= 1'b0;
            gate_base_aff_rescue_r <= 1'b0;
            gate_base_arr_low_r <= 1'b0;
            struct_mem_nsr <= 32'sd0;
            struct_mem_chf <= 32'sd0;
            struct_mem_arr <= 32'sd0;
            struct_mem_aff <= 32'sd0;
            final_valid <= 1'b0;
            final_pred_class <= CLS_NSR;
            final_mem_nsr <= 32'sd0;
            final_mem_chf <= 32'sd0;
            final_mem_arr <= 32'sd0;
            final_mem_aff <= 32'sd0;
        end else begin
            final_valid <= 1'b0;

            case (final_pipe_stage)
                FM_IDLE: begin
                    if (snapshot_done) begin
                        pred_count_nsr <= count_nsr_next;
                        pred_count_chf <= count_chf_next;
                        pred_count_arr <= count_arr_next;
                        pred_count_aff <= count_aff_next;
                        sum_beat <= beat_next;
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
                        sum_ram_code <= ram_code_next;

                        dec_count_nsr <= count_nsr_next;
                        dec_count_chf <= count_chf_next;
                        dec_count_arr <= count_arr_next;
                        dec_count_aff <= count_aff_next;
                        dec_beat <= beat_next;
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
                        dec_ram_code <= ram_code_next;
                        final_pipe_chunk <= chunk_done;
                        final_pipe_stage <= FM_BASE;
                    end
                end

                FM_BASE: begin
                    base_seed_nsr <= dec_count_nsr_s;
                    base_seed_chf <= dec_count_chf_s;
                    base_seed_arr <= dec_count_arr_s;
                    base_seed_aff <= dec_count_aff_s;
                    gate_base_aff_low_r <= gate_base_aff_low;
                    gate_base_nsr_from_chf_r <= gate_base_nsr_from_chf;
                    gate_base_chf_from_aff_r <= gate_base_chf_from_aff;
                    gate_base_aff_r <= gate_base_aff;
                    gate_base_arr_r <= gate_base_arr;
                    gate_base_aff_rescue_r <= gate_base_aff_rescue;
                    gate_base_arr_low_r <= gate_base_arr_low;
                    final_pipe_stage <= FM_BASE_APPLY;
                end

                FM_BASE_APPLY: begin
                    base_mem_nsr <= base_mem_nsr_comb;
                    base_mem_chf <= base_mem_chf_comb;
                    base_mem_arr <= base_mem_arr_comb;
                    base_mem_aff <= base_mem_aff_comb;
                    final_pipe_stage <= FM_STRUCT;
                end

                FM_STRUCT: begin
                    struct_mem_nsr <= struct_mem_nsr_comb;
                    struct_mem_chf <= struct_mem_chf_comb;
                    struct_mem_arr <= struct_mem_arr_comb;
                    struct_mem_aff <= struct_mem_aff_comb;
                    final_pipe_stage <= FM_WTA;
                end

                FM_WTA: begin
                    if (final_pipe_chunk) begin
                        final_mem_nsr <= struct_mem_nsr;
                        final_mem_chf <= struct_mem_chf;
                        final_mem_arr <= struct_mem_arr;
                        final_mem_aff <= struct_mem_aff;
                        final_pred_class <= argmax_score4(struct_mem_nsr, struct_mem_chf, struct_mem_arr, struct_mem_aff);
                        final_valid <= 1'b1;
                    end
                    final_pipe_chunk <= 1'b0;
                    final_pipe_stage <= FM_IDLE;
                end

                default: begin
                    final_pipe_stage <= FM_IDLE;
                end
            endcase
        end
    end

endmodule
