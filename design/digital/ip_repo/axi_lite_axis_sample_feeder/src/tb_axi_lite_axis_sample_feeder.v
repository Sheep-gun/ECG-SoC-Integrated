`timescale 1ns / 1ps

module tb_axi_lite_axis_sample_feeder;
    localparam integer AXI_ADDR_WIDTH = 8;
    localparam integer AXI_DATA_WIDTH = 32;
    localparam integer M_AXIS_TDATA_WIDTH = 16;

    localparam [AXI_ADDR_WIDTH-1:0] ADDR_CONTROL      = 8'h00;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_STATUS       = 8'h04;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_ERROR_STATUS = 8'h08;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_SAMPLE       = 8'h10;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_WRITE_COUNT  = 8'h14;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_TX_COUNT     = 8'h18;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_TLAST_COUNT  = 8'h1c;

    reg clk = 1'b0;
    reg rstn = 1'b0;
    always #5 clk = ~clk;

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

    wire [M_AXIS_TDATA_WIDTH-1:0] tdata;
    wire tvalid;
    reg tready = 1'b0;
    wire tlast;

    integer fail_count = 0;

    axi_lite_axis_sample_feeder #(
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .M_AXIS_TDATA_WIDTH(M_AXIS_TDATA_WIDTH),
        .FIFO_DEPTH(4),
        .FIFO_ADDR_WIDTH(2)
    ) dut (
        .s_axi_aclk(clk),
        .s_axi_aresetn(rstn),
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
        .m_axis_tdata(tdata),
        .m_axis_tvalid(tvalid),
        .m_axis_tready(tready),
        .m_axis_tlast(tlast)
    );

    task check_eq;
        input [127:0] name;
        input [31:0] got;
        input [31:0] exp;
        begin
            if (got !== exp) begin
                $display("FEEDER_SMOKE_FAIL %0s got=0x%08x exp=0x%08x", name, got, exp);
                fail_count = fail_count + 1;
            end
        end
    endtask

    task axi_write;
        input [AXI_ADDR_WIDTH-1:0] addr;
        input [AXI_DATA_WIDTH-1:0] data;
        begin
            @(posedge clk);
            awaddr <= addr;
            awvalid <= 1'b1;
            wdata <= data;
            wstrb <= {(AXI_DATA_WIDTH/8){1'b1}};
            wvalid <= 1'b1;
            bready <= 1'b1;
            while (!(awvalid && awready && wvalid && wready))
                @(posedge clk);
            @(posedge clk);
            awvalid <= 1'b0;
            wvalid <= 1'b0;
            awaddr <= {AXI_ADDR_WIDTH{1'b0}};
            wdata <= {AXI_DATA_WIDTH{1'b0}};
            wstrb <= {(AXI_DATA_WIDTH/8){1'b0}};
            while (!bvalid)
                @(posedge clk);
            if (bresp != 2'b00) begin
                $display("FEEDER_SMOKE_FAIL write bresp addr=0x%02x bresp=%0d", addr, bresp);
                fail_count = fail_count + 1;
            end
            @(posedge clk);
            bready <= 1'b0;
        end
    endtask

    task axi_read;
        input [AXI_ADDR_WIDTH-1:0] addr;
        output [AXI_DATA_WIDTH-1:0] data;
        begin
            @(posedge clk);
            araddr <= addr;
            arvalid <= 1'b1;
            rready <= 1'b1;
            while (!(arvalid && arready))
                @(posedge clk);
            @(posedge clk);
            arvalid <= 1'b0;
            araddr <= {AXI_ADDR_WIDTH{1'b0}};
            while (!rvalid)
                @(posedge clk);
            data = rdata;
            if (rresp != 2'b00) begin
                $display("FEEDER_SMOKE_FAIL read rresp addr=0x%02x rresp=%0d", addr, rresp);
                fail_count = fail_count + 1;
            end
            @(posedge clk);
            rready <= 1'b0;
        end
    endtask

    task expect_axis;
        input [15:0] exp_data;
        input exp_last;
        begin
            tready <= 1'b0;
            repeat (2) @(posedge clk);
            if (!tvalid || tdata !== exp_data || tlast !== exp_last) begin
                $display("FEEDER_SMOKE_FAIL stalled axis got valid=%0d data=0x%04x last=%0d exp=0x%04x/%0d",
                    tvalid, tdata, tlast, exp_data, exp_last);
                fail_count = fail_count + 1;
            end
            tready <= 1'b1;
            @(posedge clk);
            tready <= 1'b0;
        end
    endtask

    reg [31:0] rd;

    initial begin
        repeat (8) @(posedge clk);
        rstn <= 1'b1;
        repeat (4) @(posedge clk);

        axi_read(ADDR_STATUS, rd);
        if (!rd[0] || !rd[1] || rd[2]) begin
            $display("FEEDER_SMOKE_FAIL reset status=0x%08x", rd);
            fail_count = fail_count + 1;
        end

        axi_write(ADDR_SAMPLE, 32'h0000_0123);
        axi_write(ADDR_SAMPLE, 32'h0000_0abc);
        axi_write(ADDR_SAMPLE, 32'h0001_0555);

        axi_read(ADDR_STATUS, rd);
        check_eq("fifo_count", {24'd0, rd[15:8]}, 32'd3);
        axi_read(ADDR_WRITE_COUNT, rd);
        check_eq("write_count", rd, 32'd3);

        expect_axis(16'h0123, 1'b0);
        expect_axis(16'h0abc, 1'b0);
        expect_axis(16'h0555, 1'b1);

        repeat (2) @(posedge clk);
        axi_read(ADDR_TX_COUNT, rd);
        check_eq("tx_count", rd, 32'd3);
        axi_read(ADDR_TLAST_COUNT, rd);
        check_eq("tlast_count", rd, 32'd1);
        axi_read(ADDR_ERROR_STATUS, rd);
        check_eq("error_status", rd, 32'd0);

        axi_write(ADDR_CONTROL, 32'h0000_0001);
        axi_read(ADDR_STATUS, rd);
        if (!rd[1]) begin
            $display("FEEDER_SMOKE_FAIL soft reset status=0x%08x", rd);
            fail_count = fail_count + 1;
        end

        if (fail_count == 0)
            $display("FEEDER_SMOKE_PASS");
        else
            $display("FEEDER_SMOKE_FAIL_COUNT %0d", fail_count);
        $finish;
    end

endmodule
