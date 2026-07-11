`timescale 1ns / 1ps

module tb_snn_ecg_30min_chunk_dataset #(
    parameter MAX_SAMPLES = 1800000,
    parameter MANIFEST_FILE = "",
    parameter RESULT_CSV = "",
    parameter DUT_SNAPSHOT_SAMPLES = 60000,
    parameter DUT_SNAPSHOTS_PER_CHUNK = 30,
    parameter DUT_POST_DONE_TICKS = 37,
    parameter DUT_PROFILE_EN = 1,
    parameter DUT_SAMPLE_GAP_CYCLES = 0
)();
    reg clk;
    reg rst;
    reg start;
    reg sample_valid;
    reg signed [11:0] adc_data;

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

    integer manifest_fd;
    integer out_fd;
    integer scan_count;
    integer case_id_i;
    integer expected_i;
    integer sample_count_i;
    integer sample_index;
    integer sample_gap_count;
    integer cycles;
    integer total;
    integer correct;
    integer timeout_cycles;
    reg [8*512-1:0] path;

    snn_ecg_30min_final_top #(
        .SNAPSHOT_SAMPLES(DUT_SNAPSHOT_SAMPLES),
        .SNAPSHOTS_PER_CHUNK(DUT_SNAPSHOTS_PER_CHUNK),
        .POST_DONE_TICKS(DUT_POST_DONE_TICKS),
        .PROFILE_EN(DUT_PROFILE_EN),
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

    always #5 clk = ~clk;

    task reset_top;
        begin
            @(negedge clk);
            rst = 1'b1;
            start = 1'b0;
            sample_valid = 1'b0;
            adc_data = 12'sd0;
            repeat (8) @(posedge clk);
            rst = 1'b0;
        end
    endtask

    task run_case;
        input integer case_id;
        input integer expected_class;
        input integer sample_count;
        input [8*512-1:0] mem_path;
        begin
            $readmemh(mem_path, sample_mem);
            reset_top();

            @(negedge clk);
            start = 1'b1;
            @(posedge clk);
            #1;
            @(negedge clk);
            start = 1'b0;

            sample_index = 0;
            sample_gap_count = 0;
            cycles = 0;
            timeout_cycles = (sample_count * (DUT_SAMPLE_GAP_CYCLES + 2)) + 20000;
            while ((final_valid == 1'b0) && (cycles < timeout_cycles)) begin
                @(negedge clk);
                if (sample_ready && (sample_gap_count == 0) && (sample_index < sample_count)) begin
                    sample_valid = 1'b1;
                    adc_data = sample_mem[sample_index];
                    sample_index = sample_index + 1;
                    sample_gap_count = DUT_SAMPLE_GAP_CYCLES;
                end else begin
                    sample_valid = 1'b0;
                    adc_data = 12'sd0;
                    if (sample_gap_count > 0)
                        sample_gap_count = sample_gap_count - 1;
                end
                @(posedge clk);
                #1;
                cycles = cycles + 1;
            end

            @(negedge clk);
            sample_valid = 1'b0;
            adc_data = 12'sd0;

            total = total + 1;
            if (final_valid && (final_pred_class == expected_class[1:0]))
                correct = correct + 1;

            if (!final_valid)
                $display("WARN final timeout case=%0d samples=%0d driven=%0d cycles=%0d snapshot=%0d",
                         case_id, sample_count, sample_index, cycles, snapshot_index_dbg);
            if (sample_index != sample_count)
                $display("WARN sample_count mismatch case=%0d driven=%0d expected=%0d",
                         case_id, sample_index, sample_count);
            if (final_valid && (prof_accepted_sample_counter != sample_count))
                $display("WARN profile accepted_sample mismatch case=%0d prof=%0d expected=%0d",
                         case_id, prof_accepted_sample_counter, sample_count);

            $fdisplay(out_fd, "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",
                      case_id,
                      expected_class,
                      final_valid ? final_pred_class : 2'd0,
                      final_valid && (final_pred_class == expected_class[1:0]),
                      final_valid,
                      sample_index,
                      final_mem_nsr,
                      final_mem_chf,
                      final_mem_arr,
                      final_mem_aff,
                      cycles,
                      prof_total_cycle_counter,
                      prof_busy_cycle_counter,
                      prof_run_cycle_counter,
                      prof_input_wait_cycle_counter,
                      prof_accepted_sample_counter,
                      prof_window_counter,
                      prof_decision_counter,
                      prof_last_window_latency,
                      prof_max_window_latency,
                      prof_last_decision_latency);
            $display("CHUNK_RESULT case=%0d expected=%0d pred=%0d correct=%0d valid=%0d samples=%0d cycles=%0d",
                     case_id,
                     expected_class,
                     final_valid ? final_pred_class : 2'd0,
                     final_valid && (final_pred_class == expected_class[1:0]),
                     final_valid,
                     sample_index,
                     cycles);
            $display("PROFILE_RESULT case=%0d total_cycles=%0d busy_cycles=%0d run_cycles=%0d input_wait_cycles=%0d accepted_samples=%0d windows=%0d decisions=%0d last_window_latency=%0d max_window_latency=%0d last_decision_latency=%0d",
                     case_id,
                     prof_total_cycle_counter,
                     prof_busy_cycle_counter,
                     prof_run_cycle_counter,
                     prof_input_wait_cycle_counter,
                     prof_accepted_sample_counter,
                     prof_window_counter,
                     prof_decision_counter,
                     prof_last_window_latency,
                     prof_max_window_latency,
                     prof_last_decision_latency);
        end
    endtask

    initial begin
        clk = 1'b0;
        rst = 1'b1;
        start = 1'b0;
        sample_valid = 1'b0;
        adc_data = 12'sd0;
        total = 0;
        correct = 0;

        manifest_fd = $fopen(MANIFEST_FILE, "r");
        if (manifest_fd == 0) begin
            $display("FAIL cannot open manifest: %s", MANIFEST_FILE);
            $finish;
        end
        out_fd = $fopen(RESULT_CSV, "w");
        if (out_fd == 0) begin
            $display("FAIL cannot open result csv: %s", RESULT_CSV);
            $finish;
        end
        $fdisplay(out_fd, "case_id,expected_class,final_pred_class,correct,final_valid,samples_driven,final_mem_NSR,final_mem_CHF,final_mem_ARR,final_mem_AFF,cycles,prof_total_cycles,prof_busy_cycles,prof_run_cycles,prof_input_wait_cycles,prof_accepted_samples,prof_windows,prof_decisions,prof_last_window_latency,prof_max_window_latency,prof_last_decision_latency");

        while (!$feof(manifest_fd)) begin
            path = 0;
            scan_count = $fscanf(manifest_fd, "%d %d %d %s\n", case_id_i, expected_i, sample_count_i, path);
            if (scan_count == 4)
                run_case(case_id_i, expected_i, sample_count_i, path);
        end

        $display("CHUNK_STREAM_RESULT correct/total=%0d/%0d manifest=%0s", correct, total, MANIFEST_FILE);
        $fclose(out_fd);
        $fclose(manifest_fd);
        $finish;
    end
endmodule
