`timescale 1ns / 1ps

module tb_snn_ecg_30min_debug_case;
    parameter MAX_SAMPLES = 1800000;

    reg clk = 1'b0;
    reg rst = 1'b1;
    reg start = 1'b0;
    reg sample_valid = 1'b0;
    reg signed [11:0] adc_data = 12'sd0;

    wire sample_ready;
    wire busy;
    wire final_valid;
    wire [1:0] final_pred_class;
    wire signed [31:0] final_mem_nsr;
    wire signed [31:0] final_mem_chf;
    wire signed [31:0] final_mem_arr;
    wire signed [31:0] final_mem_aff;
    wire [5:0] snapshot_index_dbg;
    wire [63:0] prof_total_cycle_counter;
    wire [63:0] prof_busy_cycle_counter;
    wire [63:0] prof_run_cycle_counter;
    wire [63:0] prof_input_wait_cycle_counter;
    wire [63:0] prof_accepted_sample_counter;
    wire [63:0] prof_window_counter;
    wire [63:0] prof_decision_counter;
    wire [63:0] prof_last_window_latency;
    wire [63:0] prof_max_window_latency;
    wire [63:0] prof_last_decision_latency;

    reg [11:0] sample_mem [0:MAX_SAMPLES-1];
    reg [8*512-1:0] mem_path;
    integer sample_index;
    integer cycles;

    always #5 clk = ~clk;

    snn_ecg_30min_final_top #(
        .SNAPSHOT_SAMPLES(60000),
        .SNAPSHOTS_PER_CHUNK(30),
        .POST_DONE_TICKS(37),
        .PROFILE_EN(1),
        .PROF_COUNTER_W(64)
    ) dut (
        .clk(clk),
        .rst(rst),
        .start(start),
        .sample_valid(sample_valid),
        .adc_data(adc_data),
        .sample_ready(sample_ready),
        .busy(busy),
        .final_valid(final_valid),
        .final_pred_class(final_pred_class),
        .final_mem_nsr(final_mem_nsr),
        .final_mem_chf(final_mem_chf),
        .final_mem_arr(final_mem_arr),
        .final_mem_aff(final_mem_aff),
        .snapshot_index_dbg(snapshot_index_dbg),
        .prof_total_cycle_counter(prof_total_cycle_counter),
        .prof_busy_cycle_counter(prof_busy_cycle_counter),
        .prof_run_cycle_counter(prof_run_cycle_counter),
        .prof_input_wait_cycle_counter(prof_input_wait_cycle_counter),
        .prof_accepted_sample_counter(prof_accepted_sample_counter),
        .prof_window_counter(prof_window_counter),
        .prof_decision_counter(prof_decision_counter),
        .prof_last_window_latency(prof_last_window_latency),
        .prof_max_window_latency(prof_max_window_latency),
        .prof_last_decision_latency(prof_last_decision_latency)
    );

    always @(posedge clk) begin
        if (dut.final_snapshot_done) begin
            $display("SNAP_COMMIT idx=%0d pred_valid=%0d pred=%0d c24=%0d,%0d,%0d,%0d beat=%0d pnn_mis=%0d dscr_flip=%0d dscr_slope=%0d qrs=%0d qrs_w=%0d qrs_c=%0d qrs_e=%0d rbbb=%0d pre_qrs=%0d rdm_valid=%0d rdm_code=%0d ram_count=%0d ram_sum=%0d",
                     dut.snapshot_index,
                     dut.final_pred_valid,
                     dut.final_pred_class_for_commit,
                     dut.c24_mem_nsr,
                     dut.c24_mem_chf,
                     dut.c24_mem_arr,
                     dut.c24_mem_aff,
                     dut.beat_count,
                     dut.pnn_mismatch_count,
                     dut.dscr_flip_count,
                     dut.dscr_slope_count,
                     dut.qrs_maf_count,
                     dut.qrs_width_abn_count,
                     dut.qrs_complex_abn_count,
                     dut.qrs_energy_abn_count,
                     dut.rbbb_delay_like_count,
                     dut.pre_qrs_bump_count,
                     dut.rdm_valid_count,
                     dut.rdm_code_sum,
                     dut.ram_code_count,
                     dut.ram_code_sum);
        end
    end

    initial begin
        mem_path = "../../../fullrec_afe_30min_annotation_valid_balanced/test/NSR/18184/18184_30min_w031.mem";
        if (!$value$plusargs("MEM=%s", mem_path)) begin
            $display("DEBUG_CASE_INFO using default MEM=%s", mem_path);
        end
        $readmemh(mem_path, sample_mem);
        repeat (8) @(posedge clk);
        rst = 1'b0;
        @(negedge clk);
        start = 1'b1;
        @(posedge clk);
        #1;
        @(negedge clk);
        start = 1'b0;

        sample_index = 0;
        cycles = 0;
        while ((final_valid == 1'b0) && (cycles < MAX_SAMPLES + 20000)) begin
            @(negedge clk);
            if (sample_ready && (sample_index < MAX_SAMPLES)) begin
                sample_valid = 1'b1;
                adc_data = sample_mem[sample_index];
                sample_index = sample_index + 1;
            end else begin
                sample_valid = 1'b0;
                adc_data = 12'sd0;
            end
            @(posedge clk);
            #1;
            cycles = cycles + 1;
        end

        $display("DEBUG_FINAL valid=%0d pred=%0d mem=%0d,%0d,%0d,%0d samples=%0d cycles=%0d",
                 final_valid, final_pred_class,
                 final_mem_nsr, final_mem_chf, final_mem_arr, final_mem_aff,
                 sample_index, cycles);
        $finish;
    end
endmodule
