`timescale 1ns / 1ps

module tb_snn_ecg_axi_smoke;

    localparam integer AXI_ADDR_WIDTH = 12;
    localparam integer AXI_DATA_WIDTH = 32;
    localparam integer S_AXIS_TDATA_WIDTH = 16;
    localparam integer SNAPSHOT_SAMPLES = 8;
    localparam integer SNAPSHOTS_PER_CHUNK = 2;
    localparam integer TOTAL_SAMPLES = SNAPSHOT_SAMPLES * SNAPSHOTS_PER_CHUNK;

    localparam [AXI_ADDR_WIDTH-1:0] ADDR_CONTROL          = 12'h000;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_STATUS           = 12'h004;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_ERROR_STATUS     = 12'h008;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_TOTAL_SAMPLES    = 12'h010;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_SAMPLES_ACCEPTED = 12'h014;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_SAMPLES_CONSUMED = 12'h018;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_FINAL_PRED       = 12'h030;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_PROFILE_ACCEPTED = 12'h120;

    reg clk = 1'b0;
    reg aresetn = 1'b0;

    reg [AXI_ADDR_WIDTH-1:0] awaddr = {AXI_ADDR_WIDTH{1'b0}};
    reg [2:0] awprot = 3'b000;
    reg awvalid = 1'b0;
    wire awready;
    reg [AXI_DATA_WIDTH-1:0] wdata = {AXI_DATA_WIDTH{1'b0}};
    reg [(AXI_DATA_WIDTH/8)-1:0] wstrb = {(AXI_DATA_WIDTH/8){1'b0}};
    reg wvalid = 1'b0;
    wire wready;
    wire [1:0] bresp;
    wire bvalid;
    reg bready = 1'b0;

    reg [AXI_ADDR_WIDTH-1:0] araddr = {AXI_ADDR_WIDTH{1'b0}};
    reg [2:0] arprot = 3'b000;
    reg arvalid = 1'b0;
    wire arready;
    wire [AXI_DATA_WIDTH-1:0] rdata;
    wire [1:0] rresp;
    wire rvalid;
    reg rready = 1'b0;

    reg [S_AXIS_TDATA_WIDTH-1:0] tdata = {S_AXIS_TDATA_WIDTH{1'b0}};
    reg tvalid = 1'b0;
    wire tready;
    reg tlast = 1'b0;
    wire irq;

    integer fail_count = 0;
    integer idx;
    reg [31:0] rd;
    reg [31:0] held_rdata;

    always #5 clk = ~clk;

    snn_ecg_axi_lite_stream_top #(
        .S_AXIS_TDATA_WIDTH(S_AXIS_TDATA_WIDTH),
        .SNAPSHOT_SAMPLES(SNAPSHOT_SAMPLES),
        .SNAPSHOTS_PER_CHUNK(SNAPSHOTS_PER_CHUNK),
        .POST_DONE_TICKS(37),
        .PROFILE_EN(1),
        .TLAST_CHECK_EN(1)
    ) dut (
        .s_axi_aclk(clk),
        .s_axi_aresetn(aresetn),
        .s_axi_awaddr(awaddr),
        .s_axi_awprot(awprot),
        .s_axi_awvalid(awvalid),
        .s_axi_awready(awready),
        .s_axi_wdata(wdata),
        .s_axi_wstrb(wstrb),
        .s_axi_wvalid(wvalid),
        .s_axi_wready(wready),
        .s_axi_bresp(bresp),
        .s_axi_bvalid(bvalid),
        .s_axi_bready(bready),
        .s_axi_araddr(araddr),
        .s_axi_arprot(arprot),
        .s_axi_arvalid(arvalid),
        .s_axi_arready(arready),
        .s_axi_rdata(rdata),
        .s_axi_rresp(rresp),
        .s_axi_rvalid(rvalid),
        .s_axi_rready(rready),
        .s_axis_tdata(tdata),
        .s_axis_tvalid(tvalid),
        .s_axis_tready(tready),
        .s_axis_tlast(tlast),
        .irq(irq)
    );

    task check_eq;
        input [255:0] name;
        input [31:0] got;
        input [31:0] exp;
        begin
            if (got !== exp) begin
                $display("AXI_SMOKE_FAIL %0s got=0x%08x exp=0x%08x", name, got, exp);
                fail_count = fail_count + 1;
            end
        end
    endtask

    task axi_write;
        input [AXI_ADDR_WIDTH-1:0] addr;
        input [31:0] data;
        input integer skew_mode;
        begin
            @(posedge clk);
            awaddr <= addr;
            awprot <= 3'b000;
            wdata <= data;
            wstrb <= 4'hf;
            bready <= 1'b1;
            if (skew_mode == 1) begin
                awvalid <= 1'b1;
                wait (awready);
                @(posedge clk);
                awvalid <= 1'b0;
                repeat (2) @(posedge clk);
                wvalid <= 1'b1;
                wait (wready);
                @(posedge clk);
                wvalid <= 1'b0;
            end else if (skew_mode == 2) begin
                wvalid <= 1'b1;
                wait (wready);
                @(posedge clk);
                wvalid <= 1'b0;
                repeat (2) @(posedge clk);
                awvalid <= 1'b1;
                wait (awready);
                @(posedge clk);
                awvalid <= 1'b0;
            end else begin
                awvalid <= 1'b1;
                wvalid <= 1'b1;
                while (!(awready && wready)) @(posedge clk);
                @(posedge clk);
                awvalid <= 1'b0;
                wvalid <= 1'b0;
            end
            wait (bvalid);
            if (bresp !== 2'b00) begin
                $display("AXI_SMOKE_FAIL write bresp addr=0x%03x bresp=%0d", addr, bresp);
                fail_count = fail_count + 1;
            end
            @(posedge clk);
            bready <= 1'b0;
            awaddr <= {AXI_ADDR_WIDTH{1'b0}};
            awprot <= 3'b000;
            wdata <= 32'd0;
            wstrb <= 4'd0;
        end
    endtask

    task axi_read;
        input [AXI_ADDR_WIDTH-1:0] addr;
        output [31:0] data;
        begin
            @(posedge clk);
            araddr <= addr;
            arprot <= 3'b000;
            arvalid <= 1'b1;
            wait (arready);
            @(posedge clk);
            arvalid <= 1'b0;
            wait (rvalid);
            held_rdata = rdata;
            repeat (3) begin
                @(posedge clk);
                if (rdata !== held_rdata) begin
                    $display("AXI_SMOKE_FAIL rdata changed while stalled addr=0x%03x", addr);
                    fail_count = fail_count + 1;
                end
            end
            data = rdata;
            if (rresp !== 2'b00) begin
                $display("AXI_SMOKE_FAIL read rresp addr=0x%03x rresp=%0d", addr, rresp);
                fail_count = fail_count + 1;
            end
            rready <= 1'b1;
            @(posedge clk);
            rready <= 1'b0;
            araddr <= {AXI_ADDR_WIDTH{1'b0}};
            arprot <= 3'b000;
        end
    endtask

    task axis_send_sample;
        input [S_AXIS_TDATA_WIDTH-1:0] sample;
        input last;
        begin
            @(posedge clk);
            tdata <= sample;
            tlast <= last;
            tvalid <= 1'b1;
            while (!tready) begin
                @(posedge clk);
                if (tdata !== sample) begin
                    $display("AXI_SMOKE_FAIL tdata changed while stalled");
                    fail_count = fail_count + 1;
                end
            end
            @(posedge clk);
            tvalid <= 1'b0;
            tlast <= 1'b0;
            tdata <= {S_AXIS_TDATA_WIDTH{1'b0}};
        end
    endtask

    task axis_send_burst;
        integer sent;
        begin
            sent = 0;
            @(posedge clk);
            tdata <= {S_AXIS_TDATA_WIDTH{1'b0}};
            tlast <= (TOTAL_SAMPLES == 1);
            tvalid <= 1'b1;
            while (sent < TOTAL_SAMPLES) begin
                @(posedge clk);
                if (tvalid && tready) begin
                    sent = sent + 1;
                    if (sent < TOTAL_SAMPLES) begin
                        tdata <= sent[S_AXIS_TDATA_WIDTH-1:0];
                        tlast <= (sent == (TOTAL_SAMPLES - 1));
                    end else begin
                        tvalid <= 1'b0;
                        tlast <= 1'b0;
                        tdata <= {S_AXIS_TDATA_WIDTH{1'b0}};
                    end
                end
            end
        end
    endtask

    initial begin
        repeat (8) @(posedge clk);
        aresetn <= 1'b1;
        repeat (8) @(posedge clk);

        check_eq("tready_reset", {31'd0, tready}, 32'd0);
        axi_read(ADDR_TOTAL_SAMPLES, rd);
        check_eq("total_samples", rd, TOTAL_SAMPLES);
        axi_read(ADDR_STATUS, rd);
        check_eq("status_after_reset_busy_done", rd[1:0], 32'd0);

        axi_write(ADDR_CONTROL, 32'h00000001, 0);
        axi_write(ADDR_CONTROL, 32'h00000001, 1);
        axi_read(ADDR_ERROR_STATUS, rd);
        if (rd[0] !== 1'b1) begin
            $display("AXI_SMOKE_FAIL start_while_busy error not set error=0x%08x", rd);
            fail_count = fail_count + 1;
        end
        axi_write(ADDR_CONTROL, 32'h00000010, 2);

        axis_send_burst();

        for (idx = 0; idx < 10000; idx = idx + 1) begin
            if (irq)
                idx = 10000;
            @(posedge clk);
        end
        if (!irq) begin
            $display("AXI_SMOKE_FAIL irq/done timeout");
            fail_count = fail_count + 1;
        end

        axi_read(ADDR_STATUS, rd);
        if (rd[1] !== 1'b1 || rd[2] !== 1'b1) begin
            $display("AXI_SMOKE_FAIL done/result status=0x%08x", rd);
            fail_count = fail_count + 1;
        end
        axi_read(ADDR_SAMPLES_ACCEPTED, rd);
        check_eq("samples_accepted", rd, TOTAL_SAMPLES);
        axi_read(ADDR_SAMPLES_CONSUMED, rd);
        check_eq("samples_consumed", rd, TOTAL_SAMPLES);
        axi_read(ADDR_PROFILE_ACCEPTED, rd);
        check_eq("profile_accepted_lo", rd, TOTAL_SAMPLES);
        axi_read(ADDR_FINAL_PRED, rd);
        if (rd[0] !== 1'b1 || rd[8] !== 1'b1) begin
            $display("AXI_SMOKE_FAIL final_pred register=0x%08x", rd);
            fail_count = fail_count + 1;
        end

        axi_write(ADDR_CONTROL, 32'h00000004, 0);
        axi_read(ADDR_STATUS, rd);
        if (rd[1] !== 1'b0 || rd[2] !== 1'b0) begin
            $display("AXI_SMOKE_FAIL clear_done status=0x%08x", rd);
            fail_count = fail_count + 1;
        end

        if (fail_count == 0)
            $display("AXI_SMOKE_PASS");
        else
            $display("AXI_SMOKE_FAIL_COUNT %0d", fail_count);
        $finish;
    end

endmodule
