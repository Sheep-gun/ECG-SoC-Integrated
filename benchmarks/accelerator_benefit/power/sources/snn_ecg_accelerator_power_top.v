`timescale 1ns / 1ps

// Power-analysis boundary containing only the locked accelerator hierarchy.
// ECG stimulus, UART, MicroBlaze, sample memories, LEDs, and synthetic LFSRs
// are outside this module.
module snn_ecg_accelerator_power_top (
    input clk,
    input rst,
    input start,
    input sample_valid,
    input signed [11:0] adc_data,
    output sample_ready,
    output busy,
    output final_valid,
    output [1:0] final_pred_class,
    output signed [31:0] final_mem_nsr,
    output signed [31:0] final_mem_chf,
    output signed [31:0] final_mem_arr,
    output signed [31:0] final_mem_aff,
    output [5:0] snapshot_index_dbg
);
    snn_ecg_30min_final_top u_dut (
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
        .snapshot_index_dbg(snapshot_index_dbg)
    );
endmodule
