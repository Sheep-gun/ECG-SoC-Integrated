`timescale 1ns / 1ps

// Pure-RTL Nexys A7 wrapper for performance-matched 100 MHz power analysis.
// Unlike snn_ecg_v2_nexys_a7_top, the accelerator core is driven directly
// from the 100 MHz board clock; there is no generated 1 MHz core clock.
module snn_ecg_v2_nexys_a7_100mhz_top(
    input CLK100MHZ,
    input CPU_RESETN,
    input BTNC,
    output [15:0] LED,
    output CA,
    output CB,
    output CC,
    output CD,
    output CE,
    output CF,
    output CG,
    output DP,
    output [7:0] AN
);

    wire core_clk = CLK100MHZ;
    reg [1:0] rst_sync_core;
    wire rst_core;

    always @(posedge core_clk) begin
        if (!CPU_RESETN)
            rst_sync_core <= 2'b11;
        else
            rst_sync_core <= {rst_sync_core[0], 1'b0};
    end
    assign rst_core = rst_sync_core[1];

    reg btn_meta;
    reg btn_sync;
    reg btn_prev;
    wire start_pulse;

    always @(posedge core_clk) begin
        if (rst_core) begin
            btn_meta <= 1'b0;
            btn_sync <= 1'b0;
            btn_prev <= 1'b0;
        end else begin
            btn_meta <= BTNC;
            btn_sync <= btn_meta;
            btn_prev <= btn_sync;
        end
    end
    assign start_pulse = btn_sync & ~btn_prev;

    reg [15:0] lfsr;
    wire sample_ready;
    wire busy;
    wire final_valid;
    wire [1:0] final_pred_class;
    wire signed [31:0] final_mem_nsr;
    wire signed [31:0] final_mem_chf;
    wire signed [31:0] final_mem_arr;
    wire signed [31:0] final_mem_aff;
    wire [5:0] snapshot_index_dbg;
    wire sample_valid = sample_ready;
    wire signed [11:0] adc_data = lfsr[11:0];

    always @(posedge core_clk) begin
        if (rst_core)
            lfsr <= 16'hACE1;
        else if (sample_ready)
            lfsr <= {lfsr[14:0], lfsr[15] ^ lfsr[13] ^ lfsr[12] ^ lfsr[10]};
    end

    snn_ecg_30min_final_top u_dut (
        .clk(core_clk),
        .rst(rst_core),
        .start(start_pulse),
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
        .snapshot_index_dbg(snapshot_index_dbg)
    );

    assign LED[1:0] = final_pred_class;
    assign LED[2] = final_valid;
    assign LED[3] = busy;
    assign LED[9:4] = snapshot_index_dbg;
    assign LED[10] = sample_ready;
    assign LED[11] = final_mem_nsr[0];
    assign LED[12] = final_mem_chf[0];
    assign LED[13] = final_mem_arr[0];
    assign LED[14] = final_mem_aff[0];
    assign LED[15] = lfsr[15];

    assign {CA, CB, CC, CD, CE, CF, CG, DP} = 8'hff;
    assign AN = 8'hff;

endmodule
