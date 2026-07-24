`timescale 1ns / 1ps

module tb_dscr_spike_counter_equiv;
    reg clk = 1'b0;
    reg rst = 1'b1;
    reg clear = 1'b0;
    reg sample_valid = 1'b0;
    reg signed [11:0] adc_data = 12'sd0;

    wire fast_prev_valid;
    wire fast_prev_sign;
    wire fast_valid_spike;
    wire fast_flip_spike;
    wire ref_prev_valid;
    wire ref_prev_sign;
    wire ref_valid_spike;
    wire ref_flip_spike;

    integer i;
    integer seed;
    integer adc_walk;

    always #5 clk = ~clk;

    dscr_spike_counter #(
        .ADC_WIDTH(12),
        .MEM_WIDTH(16),
        .FILTER_SHIFT(4),
        .FILTER_FRAC(8),
        .SLOPE_INPUT_SHIFT(0),
        .SLOPE_LEAK(8),
        .SLOPE_THRESHOLD(8),
        .SIGN_LEAK(0),
        .SIGN_WEIGHT(1),
        .SIGN_THRESHOLD(1),
        .FAST_SLOPE_MEM_EN(1)
    ) u_fast (
        .clk(clk),
        .rst(rst),
        .clear(clear),
        .sample_valid(sample_valid),
        .adc_data(adc_data),
        .prev_slope_valid(fast_prev_valid),
        .prev_slope_sign(fast_prev_sign),
        .valid_slope_spike(fast_valid_spike),
        .sign_flip_spike(fast_flip_spike)
    );

    dscr_spike_counter #(
        .ADC_WIDTH(12),
        .MEM_WIDTH(16),
        .FILTER_SHIFT(4),
        .FILTER_FRAC(8),
        .SLOPE_INPUT_SHIFT(0),
        .SLOPE_LEAK(8),
        .SLOPE_THRESHOLD(8),
        .SIGN_LEAK(0),
        .SIGN_WEIGHT(1),
        .SIGN_THRESHOLD(1),
        .FAST_SLOPE_MEM_EN(0)
    ) u_ref (
        .clk(clk),
        .rst(rst),
        .clear(clear),
        .sample_valid(sample_valid),
        .adc_data(adc_data),
        .prev_slope_valid(ref_prev_valid),
        .prev_slope_sign(ref_prev_sign),
        .valid_slope_spike(ref_valid_spike),
        .sign_flip_spike(ref_flip_spike)
    );

    task check_equal;
        begin
            if ((fast_prev_valid !== ref_prev_valid) ||
                (fast_prev_sign !== ref_prev_sign) ||
                (fast_valid_spike !== ref_valid_spike) ||
                (fast_flip_spike !== ref_flip_spike) ||
                (u_fast.sample_seen !== u_ref.sample_seen) ||
                (u_fast.filt_mem !== u_ref.filt_mem) ||
                (u_fast.up_mem !== u_ref.up_mem) ||
                (u_fast.down_mem !== u_ref.down_mem) ||
                (u_fast.sign_mem !== u_ref.sign_mem)) begin
                $display("DSCR_EQUIV_FAIL cycle=%0d clear=%0b sample_valid=%0b adc=%0d", i, clear, sample_valid, adc_data);
                $display("fast prev=%0b/%0b spike=%0b flip=%0b filt=%0d up=%0d down=%0d sign=%0d",
                         fast_prev_valid, fast_prev_sign, fast_valid_spike, fast_flip_spike,
                         u_fast.filt_mem, u_fast.up_mem, u_fast.down_mem, u_fast.sign_mem);
                $display("ref  prev=%0b/%0b spike=%0b flip=%0b filt=%0d up=%0d down=%0d sign=%0d",
                         ref_prev_valid, ref_prev_sign, ref_valid_spike, ref_flip_spike,
                         u_ref.filt_mem, u_ref.up_mem, u_ref.down_mem, u_ref.sign_mem);
                $fatal;
            end
        end
    endtask

    initial begin
        seed = 32'h5eed1234;
        adc_walk = 0;
        repeat (8) @(posedge clk);
        rst = 1'b0;

        for (i = 0; i < 30000; i = i + 1) begin
            @(negedge clk);
            clear = ((i % 997) == 50) || ((i % 4093) == 123);
            sample_valid = (($random(seed) & 32'h7) != 0);
            if ((i % 257) == 0)
                adc_walk = -1800;
            else if ((i % 257) < 128)
                adc_walk = adc_walk + 31;
            else
                adc_walk = adc_walk - 29;

            if ((i % 31) == 0)
                adc_data = 12'sd1800;
            else if ((i % 47) == 0)
                adc_data = -12'sd1800;
            else
                adc_data = adc_walk[11:0];

            @(posedge clk);
            #1;
            check_equal();
        end

        $display("DSCR_EQUIV_PASS cycles=%0d", i);
        $finish;
    end
endmodule
