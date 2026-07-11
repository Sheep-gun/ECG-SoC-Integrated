`timescale 1ns/1ps

// Verification-only accepted-sample architectural checkpoint instrumentation.
// The hash contains persistent feature state and deliberately excludes physical
// class-score/readout pipeline staging compressed by the transaction model.
module tb_exact_cpp_sample_hash;
    parameter MAX_SAMPLES = 60000;
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

    function [63:0] fnv_byte;
        input [63:0] h;
        input [7:0] b;
        begin fnv_byte=(h ^ {56'd0,b}) * 64'd1099511628211; end
    endfunction

    function [63:0] architectural_hash;
        input unused;
        reg [63:0] h;
        reg [15:0] v16;
        reg [31:0] v32;
        begin
            h=64'd1469598103934665603;
            v16={{4{dut.u_snapshot.u_event_encoder.prev_sample[11]}},dut.u_snapshot.u_event_encoder.prev_sample};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v16={{3{dut.u_snapshot.u_event_encoder.delta[12]}},dut.u_snapshot.u_event_encoder.delta};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v16={3'd0,dut.u_snapshot.u_event_encoder.abs_delta};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_event_encoder.sample_seen});
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_event_encoder.adaptive_ready});
            h=fnv_byte(h,dut.u_snapshot.u_event_encoder.adaptive_event_th);
            v16={4'd0,dut.u_snapshot.u_qrs_detector.qrs_mem};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v16={6'd0,dut.u_snapshot.u_qrs_detector.refractory_cnt};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_pnn.token_active});
            v16={4'd0,dut.u_snapshot.u_pnn.token_age};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v16={4'd0,dut.u_snapshot.u_pnn.rr_interval};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            h=fnv_byte(h,{2'd0,dut.u_snapshot.u_pnn.predictor_id});
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_pnn.predictor_valid});
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_pnn.evaluating});
            h=fnv_byte(h,{2'd0,dut.u_snapshot.u_pnn.eval_idx});
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_rdm.prev_rr_valid});
            v16={4'd0,dut.u_snapshot.u_rdm.prev_rr};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v16={4'd0,dut.u_snapshot.u_ectopic.rr_ref};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v32={{8{dut.u_snapshot.u_dscr.filt_mem[23]}},dut.u_snapshot.u_dscr.filt_mem};
            h=fnv_byte(h,v32[7:0]); h=fnv_byte(h,v32[15:8]); h=fnv_byte(h,v32[23:16]); h=fnv_byte(h,v32[31:24]);
            v16={4'd0,dut.u_snapshot.u_dscr.up_mem};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            v16={4'd0,dut.u_snapshot.u_dscr.down_mem};
            h=fnv_byte(h,v16[7:0]); h=fnv_byte(h,v16[15:8]);
            h=fnv_byte(h,{2'd0,dut.u_snapshot.u_ram.r_peak_abs});
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_ram.post_hold_active});
            h=fnv_byte(h,dut.u_snapshot.u_ram.post_hold_cnt);
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_qrs_maf.window_active});
            h=fnv_byte(h,dut.u_snapshot.u_qrs_maf.post_count);
            h=fnv_byte(h,dut.u_snapshot.u_qrs_maf.width_ref);
            h=fnv_byte(h,{7'd0,dut.u_snapshot.u_rbbb_qrs_delay.qrs_active});
            h=fnv_byte(h,dut.u_snapshot.u_rbbb_qrs_delay.qrs_age);
            h=fnv_byte(h,dut.u_snapshot.u_rbbb_qrs_delay.rbbb_like_beat_count);
            architectural_hash=h;
        end
    endfunction

    always @(posedge clk) if(sample_valid && sample_ready) begin
        #1 $display("STATE_HASH sample=%0d hash=%016x",sample_index,architectural_hash(1'b0));
    end

    initial begin
        $readmemh("input.mem",sample_mem);
        repeat(8) @(posedge clk); rst=0;
        @(negedge clk); start=1; @(posedge clk); #1; @(negedge clk); start=0;
        sample_index=0; cycles=0; gap_count=0;
        while(sample_index<MAX_SAMPLES && cycles<200000) begin
            @(negedge clk);
            if(sample_ready && gap_count==0) begin
                sample_valid=1; adc_data=sample_mem[sample_index];
                sample_index=sample_index+1; gap_count=SAMPLE_GAP_CYCLES;
            end else begin
                sample_valid=0; adc_data=0;
                if(gap_count>0) gap_count=gap_count-1;
            end
            @(posedge clk); #1; cycles=cycles+1;
        end
        @(negedge clk); sample_valid=0;
        repeat(4) @(posedge clk);
        $display("STATE_HASH_DONE samples=%0d cycles=%0d",sample_index,cycles);
        $finish;
    end
endmodule
