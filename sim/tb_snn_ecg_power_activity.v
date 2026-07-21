`timescale 1ns / 1ps

// Activity-capture harness for the exact post-implementation power wrapper.
// The wrapper hierarchy is retained so SAIF names can be mapped to the routed
// checkpoint with: read_saif -strip_path tb_snn_ecg_power_activity/uut.
module tb_snn_ecg_power_activity;
    parameter MAX_SAMPLES = 1800000;

    reg clk;
    reg cpu_resetn;
    reg btnc;
    reg tb_sample_valid;
    reg signed [11:0] tb_adc_data;
    reg [11:0] sample_mem [0:MAX_SAMPLES-1];

    wire [15:0] led;
    wire ca;
    wire cb;
    wire cc;
    wire cd;
    wire ce;
    wire cf;
    wire cg;
    wire dp;
    wire [7:0] an;

    reg [8*1024-1:0] mem_file;
    integer sample_count;
    integer gap_cycles;
    integer require_final;
    integer expected_pred;
    integer expected_mem_nsr;
    integer expected_mem_chf;
    integer expected_mem_arr;
    integer expected_mem_aff;
    integer sample_index;
    integer gap_count;
    integer cycles;
    integer timeout_cycles;
    integer failures;

    snn_ecg_v2_nexys_a7_100mhz_top uut (
        .CLK100MHZ(clk),
        .CPU_RESETN(cpu_resetn),
        .BTNC(btnc),
        .LED(led),
        .CA(ca),
        .CB(cb),
        .CC(cc),
        .CD(cd),
        .CE(ce),
        .CF(cf),
        .CG(cg),
        .DP(dp),
        .AN(an)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        cpu_resetn = 1'b0;
        btnc = 1'b0;
        tb_sample_valid = 1'b0;
        tb_adc_data = 12'sd0;
        sample_count = 0;
        gap_cycles = 0;
        require_final = 0;
        expected_pred = 0;
        expected_mem_nsr = 0;
        expected_mem_chf = 0;
        expected_mem_arr = 0;
        expected_mem_aff = 0;
        failures = 0;

        if (!$value$plusargs("MEM%s", mem_file)) begin
            $display("FAIL missing +MEM=<path>");
            $finish;
        end
        if (!$value$plusargs("SAMPLES%d", sample_count)) begin
            $display("FAIL missing +SAMPLES=<count>");
            $finish;
        end
        if (!$value$plusargs("GAP_CYCLES%d", gap_cycles))
            gap_cycles = 0;
        if (!$value$plusargs("REQUIRE_FINAL%d", require_final))
            require_final = 0;
        if (!$value$plusargs("EXPECTED_PRED%d", expected_pred))
            expected_pred = 0;
        if (!$value$plusargs("EXPECTED_MEM_NSR%d", expected_mem_nsr))
            expected_mem_nsr = 0;
        if (!$value$plusargs("EXPECTED_MEM_CHF%d", expected_mem_chf))
            expected_mem_chf = 0;
        if (!$value$plusargs("EXPECTED_MEM_ARR%d", expected_mem_arr))
            expected_mem_arr = 0;
        if (!$value$plusargs("EXPECTED_MEM_AFF%d", expected_mem_aff))
            expected_mem_aff = 0;
        if ((sample_count <= 0) || (sample_count > MAX_SAMPLES)) begin
            $display("FAIL invalid sample count: %0d", sample_count);
            $finish;
        end

        $readmemh(mem_file, sample_mem);

        // Override only the wrapper's synthetic LFSR stimulus. The exact DUT,
        // clock, reset synchronizer, start synchronizer, and output hierarchy
        // remain identical to the implemented power target.
        force uut.sample_valid = tb_sample_valid;
        force uut.adc_data = tb_adc_data;

        repeat (12) @(posedge clk);
        cpu_resetn = 1'b1;
        repeat (12) @(posedge clk);
        @(negedge clk);
        btnc = 1'b1;
        repeat (4) @(posedge clk);
        @(negedge clk);
        btnc = 1'b0;

        cycles = 0;
        while ((uut.busy !== 1'b1) && (cycles < 1000)) begin
            @(posedge clk);
            cycles = cycles + 1;
        end
        if (uut.busy !== 1'b1) begin
            $display("FAIL DUT did not enter busy state");
            $finish;
        end

        sample_index = 0;
        gap_count = 0;
        cycles = 0;
        timeout_cycles = sample_count * (gap_cycles + 4) + 20000;
        while ((sample_index < sample_count) && (cycles < timeout_cycles)) begin
            @(negedge clk);
            if (uut.sample_ready && (gap_count == 0)) begin
                tb_sample_valid = 1'b1;
                tb_adc_data = sample_mem[sample_index];
                sample_index = sample_index + 1;
                gap_count = gap_cycles;
            end else begin
                tb_sample_valid = 1'b0;
                if (gap_count > 0)
                    gap_count = gap_count - 1;
            end
            @(posedge clk);
            cycles = cycles + 1;
        end

        @(negedge clk);
        tb_sample_valid = 1'b0;
        tb_adc_data = 12'sd0;
        if (sample_index != sample_count) begin
            $display("FAIL sample count driven=%0d expected=%0d", sample_index, sample_count);
            failures = failures + 1;
        end

        if (require_final != 0) begin
            cycles = 0;
            while ((uut.final_valid !== 1'b1) && (cycles < 20000)) begin
                @(posedge clk);
                cycles = cycles + 1;
            end
            if (uut.final_valid !== 1'b1) begin
                $display("FAIL final_valid timeout");
                failures = failures + 1;
            end else begin
                if (uut.final_pred_class != expected_pred[1:0]) failures = failures + 1;
                if (uut.final_mem_nsr != expected_mem_nsr) failures = failures + 1;
                if (uut.final_mem_chf != expected_mem_chf) failures = failures + 1;
                if (uut.final_mem_arr != expected_mem_arr) failures = failures + 1;
                if (uut.final_mem_aff != expected_mem_aff) failures = failures + 1;
                $display("ACTIVITY_FINAL pred=%0d mem=%0d/%0d/%0d/%0d expected=%0d/%0d/%0d/%0d/%0d",
                         uut.final_pred_class,
                         uut.final_mem_nsr, uut.final_mem_chf,
                         uut.final_mem_arr, uut.final_mem_aff,
                         expected_pred, expected_mem_nsr, expected_mem_chf,
                         expected_mem_arr, expected_mem_aff);
            end
        end else begin
            repeat (20) @(posedge clk);
        end

        if (failures == 0)
            $display("ACTIVITY_PASS samples=%0d gap_cycles=%0d require_final=%0d", sample_index, gap_cycles, require_final);
        else
            $display("ACTIVITY_FAIL failures=%0d samples=%0d gap_cycles=%0d", failures, sample_index, gap_cycles);
        $finish;
    end
endmodule
