`timescale 1ns/1ps

// Verification-only trace instrumentation. No locked RTL is modified.
module tb_exact_cpp_snapshot_trace;
    parameter MAX_SAMPLES = 1800000;
    parameter SAMPLE_GAP_CYCLES = 2;
    reg clk=0, rst=1, start=0, sample_valid=0;
    reg signed [11:0] adc_data=0;
    wire sample_ready, busy, final_valid;
    wire [1:0] final_pred_class;
    wire signed [31:0] final_mem_nsr,final_mem_chf,final_mem_arr,final_mem_aff;
    wire [5:0] snapshot_index_dbg;
    wire [63:0] p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,p10;
    reg [11:0] sample_mem [0:MAX_SAMPLES-1];
    integer sample_index,cycles,gap_count;
    always #5 clk=~clk;

    snn_ecg_30min_final_top #(.SNAPSHOT_SAMPLES(60000),.SNAPSHOTS_PER_CHUNK(30),
        .POST_DONE_TICKS(37),.PROFILE_EN(1),.PROF_COUNTER_W(64)) dut(
        .clk(clk),.rst(rst),.start(start),.sample_valid(sample_valid),.adc_data(adc_data),
        .sample_ready(sample_ready),.busy(busy),.final_valid(final_valid),.final_pred_class(final_pred_class),
        .final_mem_nsr(final_mem_nsr),.final_mem_chf(final_mem_chf),.final_mem_arr(final_mem_arr),.final_mem_aff(final_mem_aff),
        .snapshot_index_dbg(snapshot_index_dbg),.prof_total_cycle_counter(p0),.prof_busy_cycle_counter(p1),
        .prof_run_cycle_counter(p2),.prof_input_wait_cycle_counter(p3),.prof_accepted_sample_counter(p4),
        .prof_window_counter(p5),.prof_decision_counter(p6),.prof_last_window_latency(p7),
        .prof_max_window_latency(p8),.prof_last_decision_latency(p9));

    always @(posedge clk) if(dut.final_snapshot_done) begin
        $display("EXACT_SNAPSHOT idx=%0d accepted=%0d pred=%0d c24=%0d,%0d,%0d,%0d beat=%0d pnn_match=%0d pnn_mis=%0d dscr_flip=%0d dscr_slope=%0d ram_sum=%0d ram_count=%0d rdm_valid=%0d rdm_code=%0d ect=%0d qrs=%0d qrs_w=%0d qrs_c=%0d qrs_e=%0d rbbb=%0d rbbb_applied=%0d pre=%0d",
            dut.snapshot_index,p4,dut.final_pred_class_for_commit,dut.c24_mem_nsr,dut.c24_mem_chf,dut.c24_mem_arr,dut.c24_mem_aff,
            dut.beat_count,dut.pnn_match_count,dut.pnn_mismatch_count,dut.dscr_flip_count,dut.dscr_slope_count,
            dut.ram_code_sum,dut.ram_code_count,dut.rdm_valid_count,dut.rdm_code_sum,dut.ectopic_pair_count,
            dut.qrs_maf_count,dut.qrs_width_abn_count,dut.qrs_complex_abn_count,dut.qrs_energy_abn_count,
            dut.rbbb_delay_like_count,dut.rbbb_delay_applied_count,dut.pre_qrs_bump_count);
    end

    always @(posedge clk) if(dut.u_final.final_pipe_stage==3'd4) begin
        $display("EXACT_FINAL_STATE idx=%0d mem=%0d,%0d,%0d,%0d gates=%0d,%0d,%0d,%0d,%0d",
            dut.snapshot_index,dut.u_final.struct_mem_nsr,dut.u_final.struct_mem_chf,
            dut.u_final.struct_mem_arr,dut.u_final.struct_mem_aff,
            dut.u_final.gate_struct_aff_persistence,dut.u_final.gate_struct_nsr_clean_chf,
            dut.u_final.gate_struct_arr_over_nsr,dut.u_final.gate_struct_arr_over_aff,
            dut.u_final.gate_struct_silent_aff);
    end

    initial begin
        $readmemh("input.mem",sample_mem);
        repeat(8) @(posedge clk); rst=0;
        @(negedge clk); start=1; @(posedge clk); #1; @(negedge clk); start=0;
        sample_index=0; cycles=0; gap_count=0;
        while(!final_valid && cycles < 5425000) begin
            @(negedge clk);
            if(sample_ready && gap_count==0 && sample_index<MAX_SAMPLES) begin
                sample_valid=1; adc_data=sample_mem[sample_index]; sample_index=sample_index+1; gap_count=SAMPLE_GAP_CYCLES;
            end else begin
                sample_valid=0; adc_data=0; if(gap_count>0) gap_count=gap_count-1;
            end
            @(posedge clk); #1; cycles=cycles+1;
        end
        $display("EXACT_FINAL valid=%0d pred=%0d mem=%0d,%0d,%0d,%0d samples=%0d cycles=%0d",
            final_valid,final_pred_class,final_mem_nsr,final_mem_chf,final_mem_arr,final_mem_aff,sample_index,cycles);
        $finish;
    end
endmodule
