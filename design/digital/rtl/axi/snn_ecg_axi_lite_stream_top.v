`timescale 1ns / 1ps

module snn_ecg_axi_lite_stream_top #(
    parameter integer ADC_WIDTH = 12,
    parameter integer S_AXIS_TDATA_WIDTH = 16,
    parameter integer AXI_ADDR_WIDTH = 12,
    parameter integer AXI_DATA_WIDTH = 32,
    parameter integer SNAPSHOT_SAMPLES = 60000,
    parameter integer SNAPSHOTS_PER_CHUNK = 30,
    parameter integer POST_DONE_TICKS = 37,
    parameter integer PROFILE_EN = 1,
    parameter integer PROF_COUNTER_W = 64,
    parameter integer TLAST_CHECK_EN = 0
)(
    input wire s_axi_aclk,
    input wire s_axi_aresetn,

    input wire [AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
    input wire [2:0] s_axi_awprot,
    input wire s_axi_awvalid,
    output wire s_axi_awready,
    input wire [AXI_DATA_WIDTH-1:0] s_axi_wdata,
    input wire [(AXI_DATA_WIDTH/8)-1:0] s_axi_wstrb,
    input wire s_axi_wvalid,
    output wire s_axi_wready,
    output wire [1:0] s_axi_bresp,
    output wire s_axi_bvalid,
    input wire s_axi_bready,

    input wire [AXI_ADDR_WIDTH-1:0] s_axi_araddr,
    input wire [2:0] s_axi_arprot,
    input wire s_axi_arvalid,
    output wire s_axi_arready,
    output wire [AXI_DATA_WIDTH-1:0] s_axi_rdata,
    output wire [1:0] s_axi_rresp,
    output wire s_axi_rvalid,
    input wire s_axi_rready,

    input wire [S_AXIS_TDATA_WIDTH-1:0] s_axis_tdata,
    input wire s_axis_tvalid,
    output wire s_axis_tready,
    input wire s_axis_tlast,

    output wire irq
);

    localparam [AXI_ADDR_WIDTH-1:0] ADDR_CONTROL          = 12'h000;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_STATUS           = 12'h004;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_ERROR_STATUS     = 12'h008;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_CONFIG           = 12'h00c;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_TOTAL_SAMPLES    = 12'h010;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_SAMPLES_ACCEPTED = 12'h014;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_SAMPLES_CONSUMED = 12'h018;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_FINAL_MEM_NSR    = 12'h020;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_FINAL_MEM_CHF    = 12'h024;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_FINAL_MEM_ARR    = 12'h028;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_FINAL_MEM_AFF    = 12'h02c;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_FINAL_PRED       = 12'h030;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_PROFILE_BASE     = 12'h100;

    localparam integer TOTAL_SAMPLES = SNAPSHOT_SAMPLES * SNAPSHOTS_PER_CHUNK;

    wire rst_sync;
    reset_sync u_reset_sync (
        .clk(s_axi_aclk),
        .arstn(s_axi_aresetn),
        .rst(rst_sync)
    );

    reg aw_holding;
    reg [AXI_ADDR_WIDTH-1:0] awaddr_reg;
    reg w_holding;
    reg [AXI_DATA_WIDTH-1:0] wdata_reg;
    reg [(AXI_DATA_WIDTH/8)-1:0] wstrb_reg;
    reg [1:0] bresp_reg;
    reg bvalid_reg;
    reg [AXI_DATA_WIDTH-1:0] rdata_reg;
    reg [1:0] rresp_reg;
    reg rvalid_reg;

    wire aw_fire = s_axi_awvalid && s_axi_awready;
    wire w_fire = s_axi_wvalid && s_axi_wready;
    wire ar_fire = s_axi_arvalid && s_axi_arready;
    wire have_aw_next = aw_holding || aw_fire;
    wire have_w_next = w_holding || w_fire;
    wire do_write = have_aw_next && have_w_next && !bvalid_reg;
    wire [AXI_ADDR_WIDTH-1:0] write_addr = aw_fire ? s_axi_awaddr : awaddr_reg;
    wire [AXI_DATA_WIDTH-1:0] write_data = w_fire ? s_axi_wdata : wdata_reg;
    wire [(AXI_DATA_WIDTH/8)-1:0] write_strb = w_fire ? s_axi_wstrb : wstrb_reg;

    assign s_axi_awready = !aw_holding && !bvalid_reg;
    assign s_axi_wready = !w_holding && !bvalid_reg;
    assign s_axi_bresp = bresp_reg;
    assign s_axi_bvalid = bvalid_reg;
    assign s_axi_arready = !rvalid_reg;
    assign s_axi_rdata = rdata_reg;
    assign s_axi_rresp = rresp_reg;
    assign s_axi_rvalid = rvalid_reg;

    reg [3:0] soft_reset_count;
    wire soft_reset_active = (soft_reset_count != 4'd0);
    wire accel_reset = rst_sync || soft_reset_active;

    reg core_start_pulse;
    wire core_sample_ready;
    wire core_busy;
    wire core_final_valid;
    wire [1:0] core_final_pred_class;
    wire signed [31:0] core_final_mem_nsr;
    wire signed [31:0] core_final_mem_chf;
    wire signed [31:0] core_final_mem_arr;
    wire signed [31:0] core_final_mem_aff;
    wire [5:0] core_snapshot_index;
    wire [PROF_COUNTER_W-1:0] prof_total_cycle_counter;
    wire [PROF_COUNTER_W-1:0] prof_busy_cycle_counter;
    wire [PROF_COUNTER_W-1:0] prof_run_cycle_counter;
    wire [PROF_COUNTER_W-1:0] prof_input_wait_cycle_counter;
    wire [PROF_COUNTER_W-1:0] prof_accepted_sample_counter;
    wire [PROF_COUNTER_W-1:0] prof_window_counter;
    wire [PROF_COUNTER_W-1:0] prof_decision_counter;
    wire [PROF_COUNTER_W-1:0] prof_last_window_latency;
    wire [PROF_COUNTER_W-1:0] prof_max_window_latency;
    wire [PROF_COUNTER_W-1:0] prof_last_decision_latency;

    reg run_active;
    reg done_sticky;
    reg result_valid_reg;
    reg [1:0] final_pred_class_latched;
    reg signed [31:0] final_mem_nsr_latched;
    reg signed [31:0] final_mem_chf_latched;
    reg signed [31:0] final_mem_arr_latched;
    reg signed [31:0] final_mem_aff_latched;
    reg [31:0] samples_accepted_count;
    reg [31:0] samples_consumed_count;
    reg [31:0] error_status;

    reg [1:0] fifo_count;
    reg signed [ADC_WIDTH-1:0] fifo_data0;
    reg signed [ADC_WIDTH-1:0] fifo_data1;
    reg fifo_tlast0;
    reg fifo_tlast1;
    reg axis_tready_reg;

    wire axis_accepting = run_active && !done_sticky && (samples_accepted_count < TOTAL_SAMPLES);
    wire axis_fire = s_axis_tvalid && s_axis_tready;
    wire fifo_valid = (fifo_count != 2'd0);
    wire core_sample_valid = fifo_valid && run_active;
    wire core_sample_fire = core_sample_valid && core_sample_ready;
    wire axis_tready_next = axis_accepting && ((fifo_count == 2'd0) || core_sample_fire);
    wire signed [ADC_WIDTH-1:0] core_adc_data = fifo_data0;

    assign s_axis_tready = axis_tready_reg;
    assign irq = done_sticky;

    reg [63:0] prof_total_shadow;
    reg [63:0] prof_busy_shadow;
    reg [63:0] prof_run_shadow;
    reg [63:0] prof_input_wait_shadow;
    reg [63:0] prof_accepted_shadow;
    reg [63:0] prof_windows_shadow;
    reg [63:0] prof_decisions_shadow;
    reg [63:0] prof_last_window_shadow;
    reg [63:0] prof_max_window_shadow;
    reg [63:0] prof_last_decision_shadow;

    task latch_profile_shadow;
        begin
            prof_total_shadow <= prof_total_cycle_counter[63:0];
            prof_busy_shadow <= prof_busy_cycle_counter[63:0];
            prof_run_shadow <= prof_run_cycle_counter[63:0];
            prof_input_wait_shadow <= prof_input_wait_cycle_counter[63:0];
            prof_accepted_shadow <= prof_accepted_sample_counter[63:0];
            prof_windows_shadow <= prof_window_counter[63:0];
            prof_decisions_shadow <= prof_decision_counter[63:0];
            prof_last_window_shadow <= prof_last_window_latency[63:0];
            prof_max_window_shadow <= prof_max_window_latency[63:0];
            prof_last_decision_shadow <= prof_last_decision_latency[63:0];
        end
    endtask

    function [31:0] read_reg;
        input [AXI_ADDR_WIDTH-1:0] addr;
        begin
            case (addr)
                ADDR_CONTROL: read_reg = 32'd0;
                ADDR_STATUS: begin
                    read_reg = 32'd0;
                    read_reg[0] = core_busy;
                    read_reg[1] = done_sticky;
                    read_reg[2] = result_valid_reg;
                    read_reg[3] = core_sample_ready;
                    read_reg[4] = axis_accepting;
                    read_reg[5] = fifo_valid;
                    read_reg[7:6] = fifo_count;
                    read_reg[13:8] = core_snapshot_index;
                    read_reg[17:16] = final_pred_class_latched;
                    read_reg[18] = core_final_valid;
                    read_reg[19] = run_active;
                end
                ADDR_ERROR_STATUS: read_reg = error_status;
                ADDR_CONFIG: read_reg = {16'hec60, 4'd1, 3'd0, TLAST_CHECK_EN[0], PROFILE_EN[0], ADC_WIDTH[3:0], S_AXIS_TDATA_WIDTH[3:0]};
                ADDR_TOTAL_SAMPLES: read_reg = TOTAL_SAMPLES[31:0];
                ADDR_SAMPLES_ACCEPTED: read_reg = samples_accepted_count;
                ADDR_SAMPLES_CONSUMED: read_reg = samples_consumed_count;
                ADDR_FINAL_MEM_NSR: read_reg = final_mem_nsr_latched;
                ADDR_FINAL_MEM_CHF: read_reg = final_mem_chf_latched;
                ADDR_FINAL_MEM_ARR: read_reg = final_mem_arr_latched;
                ADDR_FINAL_MEM_AFF: read_reg = final_mem_aff_latched;
                ADDR_FINAL_PRED: begin
                    read_reg = 32'd0;
                    read_reg[0] = result_valid_reg;
                    read_reg[2:1] = final_pred_class_latched;
                    read_reg[8] = done_sticky;
                end
                ADDR_PROFILE_BASE + 12'h000: read_reg = prof_total_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h004: read_reg = prof_total_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h008: read_reg = prof_busy_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h00c: read_reg = prof_busy_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h010: read_reg = prof_run_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h014: read_reg = prof_run_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h018: read_reg = prof_input_wait_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h01c: read_reg = prof_input_wait_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h020: read_reg = prof_accepted_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h024: read_reg = prof_accepted_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h028: read_reg = prof_windows_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h02c: read_reg = prof_windows_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h030: read_reg = prof_decisions_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h034: read_reg = prof_decisions_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h038: read_reg = prof_last_window_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h03c: read_reg = prof_last_window_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h040: read_reg = prof_max_window_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h044: read_reg = prof_max_window_shadow[63:32];
                ADDR_PROFILE_BASE + 12'h048: read_reg = prof_last_decision_shadow[31:0];
                ADDR_PROFILE_BASE + 12'h04c: read_reg = prof_last_decision_shadow[63:32];
                default: read_reg = 32'd0;
            endcase
        end
    endfunction

    function valid_read_addr;
        input [AXI_ADDR_WIDTH-1:0] addr;
        begin
            case (addr)
                ADDR_CONTROL,
                ADDR_STATUS,
                ADDR_ERROR_STATUS,
                ADDR_CONFIG,
                ADDR_TOTAL_SAMPLES,
                ADDR_SAMPLES_ACCEPTED,
                ADDR_SAMPLES_CONSUMED,
                ADDR_FINAL_MEM_NSR,
                ADDR_FINAL_MEM_CHF,
                ADDR_FINAL_MEM_ARR,
                ADDR_FINAL_MEM_AFF,
                ADDR_FINAL_PRED,
                ADDR_PROFILE_BASE + 12'h000,
                ADDR_PROFILE_BASE + 12'h004,
                ADDR_PROFILE_BASE + 12'h008,
                ADDR_PROFILE_BASE + 12'h00c,
                ADDR_PROFILE_BASE + 12'h010,
                ADDR_PROFILE_BASE + 12'h014,
                ADDR_PROFILE_BASE + 12'h018,
                ADDR_PROFILE_BASE + 12'h01c,
                ADDR_PROFILE_BASE + 12'h020,
                ADDR_PROFILE_BASE + 12'h024,
                ADDR_PROFILE_BASE + 12'h028,
                ADDR_PROFILE_BASE + 12'h02c,
                ADDR_PROFILE_BASE + 12'h030,
                ADDR_PROFILE_BASE + 12'h034,
                ADDR_PROFILE_BASE + 12'h038,
                ADDR_PROFILE_BASE + 12'h03c,
                ADDR_PROFILE_BASE + 12'h040,
                ADDR_PROFILE_BASE + 12'h044,
                ADDR_PROFILE_BASE + 12'h048,
                ADDR_PROFILE_BASE + 12'h04c: valid_read_addr = 1'b1;
                default: valid_read_addr = 1'b0;
            endcase
        end
    endfunction

    wire write_control = do_write && (write_addr == ADDR_CONTROL) && write_strb[0];
    wire write_error_status = do_write && (write_addr == ADDR_ERROR_STATUS);
    wire write_addr_ok = (write_addr == ADDR_CONTROL) || (write_addr == ADDR_ERROR_STATUS);
    wire ctrl_start_req = write_control && write_data[0];
    wire ctrl_soft_reset_req = write_control && write_data[1];
    wire ctrl_clear_done_req = write_control && write_data[2];
    wire ctrl_profile_snapshot_req = write_control && write_data[3];
    wire ctrl_clear_errors_req = write_control && write_data[4];
    wire accepted_start = ctrl_start_req && !ctrl_soft_reset_req && !run_active && !core_busy && !soft_reset_active;

    always @(posedge s_axi_aclk) begin
        if (rst_sync) begin
            aw_holding <= 1'b0;
            awaddr_reg <= {AXI_ADDR_WIDTH{1'b0}};
            w_holding <= 1'b0;
            wdata_reg <= {AXI_DATA_WIDTH{1'b0}};
            wstrb_reg <= {(AXI_DATA_WIDTH/8){1'b0}};
            bresp_reg <= 2'b00;
            bvalid_reg <= 1'b0;
            rdata_reg <= {AXI_DATA_WIDTH{1'b0}};
            rresp_reg <= 2'b00;
            rvalid_reg <= 1'b0;
        end else begin
            if (aw_fire && !do_write) begin
                aw_holding <= 1'b1;
                awaddr_reg <= s_axi_awaddr;
            end else if (do_write) begin
                aw_holding <= 1'b0;
            end

            if (w_fire && !do_write) begin
                w_holding <= 1'b1;
                wdata_reg <= s_axi_wdata;
                wstrb_reg <= s_axi_wstrb;
            end else if (do_write) begin
                w_holding <= 1'b0;
            end

            if (do_write) begin
                bvalid_reg <= 1'b1;
                bresp_reg <= write_addr_ok ? 2'b00 : 2'b10;
            end else if (bvalid_reg && s_axi_bready) begin
                bvalid_reg <= 1'b0;
                bresp_reg <= 2'b00;
            end

            if (ar_fire) begin
                rvalid_reg <= 1'b1;
                rdata_reg <= read_reg(s_axi_araddr);
                rresp_reg <= valid_read_addr(s_axi_araddr) ? 2'b00 : 2'b10;
            end else if (rvalid_reg && s_axi_rready) begin
                rvalid_reg <= 1'b0;
                rresp_reg <= 2'b00;
            end
        end
    end

    always @(posedge s_axi_aclk) begin
        if (rst_sync) begin
            soft_reset_count <= 4'd0;
        end else if (ctrl_soft_reset_req) begin
            soft_reset_count <= 4'd4;
        end else if (soft_reset_count != 4'd0) begin
            soft_reset_count <= soft_reset_count - 4'd1;
        end
    end

    always @(posedge s_axi_aclk) begin
        if (rst_sync || ctrl_soft_reset_req) begin
            core_start_pulse <= 1'b0;
            run_active <= 1'b0;
            done_sticky <= 1'b0;
            result_valid_reg <= 1'b0;
            final_pred_class_latched <= 2'd0;
            final_mem_nsr_latched <= 32'sd0;
            final_mem_chf_latched <= 32'sd0;
            final_mem_arr_latched <= 32'sd0;
            final_mem_aff_latched <= 32'sd0;
            samples_accepted_count <= 32'd0;
            samples_consumed_count <= 32'd0;
            error_status <= 32'd0;
            fifo_count <= 2'd0;
            fifo_data0 <= {ADC_WIDTH{1'b0}};
            fifo_data1 <= {ADC_WIDTH{1'b0}};
            fifo_tlast0 <= 1'b0;
            fifo_tlast1 <= 1'b0;
            axis_tready_reg <= 1'b0;
            prof_total_shadow <= 64'd0;
            prof_busy_shadow <= 64'd0;
            prof_run_shadow <= 64'd0;
            prof_input_wait_shadow <= 64'd0;
            prof_accepted_shadow <= 64'd0;
            prof_windows_shadow <= 64'd0;
            prof_decisions_shadow <= 64'd0;
            prof_last_window_shadow <= 64'd0;
            prof_max_window_shadow <= 64'd0;
            prof_last_decision_shadow <= 64'd0;
        end else if (soft_reset_active) begin
            core_start_pulse <= 1'b0;
            run_active <= 1'b0;
            fifo_count <= 2'd0;
            axis_tready_reg <= 1'b0;
        end else begin
            core_start_pulse <= 1'b0;
            axis_tready_reg <= axis_tready_next;

            if (write_error_status)
                error_status <= error_status & ~write_data;
            if (ctrl_clear_errors_req)
                error_status <= 32'd0;

            if (ctrl_clear_done_req) begin
                done_sticky <= 1'b0;
                result_valid_reg <= 1'b0;
            end

            if (ctrl_start_req && !accepted_start)
                error_status[0] <= 1'b1;

            if (accepted_start) begin
                core_start_pulse <= 1'b1;
                run_active <= 1'b1;
                done_sticky <= 1'b0;
                result_valid_reg <= 1'b0;
                samples_accepted_count <= 32'd0;
                samples_consumed_count <= 32'd0;
                fifo_count <= 2'd0;
                axis_tready_reg <= 1'b0;
                error_status <= 32'd0;
                prof_total_shadow <= 64'd0;
                prof_busy_shadow <= 64'd0;
                prof_run_shadow <= 64'd0;
                prof_input_wait_shadow <= 64'd0;
                prof_accepted_shadow <= 64'd0;
                prof_windows_shadow <= 64'd0;
                prof_decisions_shadow <= 64'd0;
                prof_last_window_shadow <= 64'd0;
                prof_max_window_shadow <= 64'd0;
                prof_last_decision_shadow <= 64'd0;
            end

            if (axis_fire) begin
                samples_accepted_count <= samples_accepted_count + 32'd1;
                if ((TLAST_CHECK_EN != 0) && s_axis_tlast &&
                    (samples_accepted_count != (TOTAL_SAMPLES[31:0] - 32'd1)))
                    error_status[1] <= 1'b1;
                if ((TLAST_CHECK_EN != 0) && !s_axis_tlast &&
                    (samples_accepted_count == (TOTAL_SAMPLES[31:0] - 32'd1)))
                    error_status[2] <= 1'b1;
            end else if (s_axis_tvalid && run_active &&
                         (samples_accepted_count >= TOTAL_SAMPLES[31:0])) begin
                error_status[3] <= 1'b1;
            end

            if (core_sample_fire)
                samples_consumed_count <= samples_consumed_count + 32'd1;

            case ({core_sample_fire, axis_fire})
                2'b01: begin
                    if (fifo_count == 2'd0) begin
                        fifo_data0 <= s_axis_tdata[ADC_WIDTH-1:0];
                        fifo_tlast0 <= s_axis_tlast;
                        fifo_count <= 2'd1;
                    end else if (fifo_count == 2'd1) begin
                        fifo_data1 <= s_axis_tdata[ADC_WIDTH-1:0];
                        fifo_tlast1 <= s_axis_tlast;
                        fifo_count <= 2'd2;
                    end
                end
                2'b10: begin
                    if (fifo_count == 2'd1) begin
                        fifo_count <= 2'd0;
                    end else if (fifo_count == 2'd2) begin
                        fifo_data0 <= fifo_data1;
                        fifo_tlast0 <= fifo_tlast1;
                        fifo_count <= 2'd1;
                    end
                end
                2'b11: begin
                    if (fifo_count == 2'd1) begin
                        fifo_data0 <= s_axis_tdata[ADC_WIDTH-1:0];
                        fifo_tlast0 <= s_axis_tlast;
                        fifo_count <= 2'd1;
                    end else if (fifo_count == 2'd2) begin
                        fifo_data0 <= fifo_data1;
                        fifo_tlast0 <= fifo_tlast1;
                        fifo_data1 <= s_axis_tdata[ADC_WIDTH-1:0];
                        fifo_tlast1 <= s_axis_tlast;
                        fifo_count <= 2'd2;
                    end
                end
                default: begin
                end
            endcase

            if (core_final_valid) begin
                done_sticky <= 1'b1;
                result_valid_reg <= 1'b1;
                run_active <= 1'b0;
                final_pred_class_latched <= core_final_pred_class;
                final_mem_nsr_latched <= core_final_mem_nsr;
                final_mem_chf_latched <= core_final_mem_chf;
                final_mem_arr_latched <= core_final_mem_arr;
                final_mem_aff_latched <= core_final_mem_aff;
                latch_profile_shadow();
            end else if (ctrl_profile_snapshot_req) begin
                latch_profile_shadow();
            end
        end
    end

    snn_ecg_30min_final_top #(
        .ADC_WIDTH(ADC_WIDTH),
        .SNAPSHOT_SAMPLES(SNAPSHOT_SAMPLES),
        .SNAPSHOTS_PER_CHUNK(SNAPSHOTS_PER_CHUNK),
        .POST_DONE_TICKS(POST_DONE_TICKS),
        .PROFILE_EN(PROFILE_EN),
        .PROF_COUNTER_W(PROF_COUNTER_W)
    ) u_core (
        .clk(s_axi_aclk),
        .rst(accel_reset),
        .start(core_start_pulse),
        .sample_valid(core_sample_valid),
        .adc_data(core_adc_data),
        .sample_ready(core_sample_ready),
        .busy(core_busy),
        .final_valid(core_final_valid),
        .final_pred_class(core_final_pred_class),
        .final_mem_nsr(core_final_mem_nsr),
        .final_mem_chf(core_final_mem_chf),
        .final_mem_arr(core_final_mem_arr),
        .final_mem_aff(core_final_mem_aff),
        .snapshot_index_dbg(core_snapshot_index),
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

endmodule
