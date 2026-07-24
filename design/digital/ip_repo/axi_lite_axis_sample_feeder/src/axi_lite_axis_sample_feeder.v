`timescale 1ns / 1ps

module axi_lite_axis_sample_feeder #(
    parameter integer AXI_ADDR_WIDTH = 8,
    parameter integer AXI_DATA_WIDTH = 32,
    parameter integer M_AXIS_TDATA_WIDTH = 16,
    parameter integer FIFO_DEPTH = 16,
    parameter integer FIFO_ADDR_WIDTH = 4
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

    output wire [M_AXIS_TDATA_WIDTH-1:0] m_axis_tdata,
    output wire m_axis_tvalid,
    input wire m_axis_tready,
    output wire m_axis_tlast
);

    localparam [AXI_ADDR_WIDTH-1:0] ADDR_CONTROL      = 8'h00;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_STATUS       = 8'h04;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_ERROR_STATUS = 8'h08;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_CONFIG       = 8'h0c;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_SAMPLE       = 8'h10;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_WRITE_COUNT  = 8'h14;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_TX_COUNT     = 8'h18;
    localparam [AXI_ADDR_WIDTH-1:0] ADDR_TLAST_COUNT  = 8'h1c;

    localparam [1:0] AXI_RESP_OKAY   = 2'b00;
    localparam [1:0] AXI_RESP_SLVERR = 2'b10;
    localparam integer FIFO_COUNT_WIDTH = FIFO_ADDR_WIDTH + 1;

    reg aw_holding;
    reg [AXI_ADDR_WIDTH-1:0] awaddr_reg;
    reg w_holding;
    reg [AXI_DATA_WIDTH-1:0] wdata_reg;
    reg [(AXI_DATA_WIDTH/8)-1:0] wstrb_reg;
    reg bvalid_reg;
    reg [1:0] bresp_reg;
    reg rvalid_reg;
    reg [1:0] rresp_reg;
    reg [AXI_DATA_WIDTH-1:0] rdata_reg;

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
    assign s_axi_bvalid = bvalid_reg;
    assign s_axi_bresp = bresp_reg;
    assign s_axi_arready = !rvalid_reg;
    assign s_axi_rvalid = rvalid_reg;
    assign s_axi_rresp = rresp_reg;
    assign s_axi_rdata = rdata_reg;

    reg [M_AXIS_TDATA_WIDTH-1:0] fifo_data [0:FIFO_DEPTH-1];
    reg fifo_last [0:FIFO_DEPTH-1];
    reg [FIFO_ADDR_WIDTH-1:0] wr_ptr;
    reg [FIFO_ADDR_WIDTH-1:0] rd_ptr;
    reg [FIFO_COUNT_WIDTH-1:0] fifo_count;
    reg [31:0] write_count;
    reg [31:0] tx_count;
    reg [31:0] tlast_count;
    reg [31:0] error_status;

    wire fifo_empty = (fifo_count == {FIFO_COUNT_WIDTH{1'b0}});
    wire fifo_full = (fifo_count == FIFO_DEPTH[FIFO_COUNT_WIDTH-1:0]);
    wire axis_pop = !fifo_empty && m_axis_tready;
    wire write_sample = do_write && (write_addr == ADDR_SAMPLE) && (write_strb != {(AXI_DATA_WIDTH/8){1'b0}});
    wire sample_push_ok = write_sample && (!fifo_full || axis_pop);
    wire sample_overflow = write_sample && fifo_full && !axis_pop;
    wire control_write = do_write && (write_addr == ADDR_CONTROL);
    wire control_soft_reset = control_write && write_data[0];
    wire control_clear_errors = control_write && write_data[1];
    wire control_clear_counters = control_write && write_data[2];

    assign m_axis_tvalid = !fifo_empty;
    assign m_axis_tdata = fifo_data[rd_ptr];
    assign m_axis_tlast = fifo_last[rd_ptr];

    function [FIFO_ADDR_WIDTH-1:0] ptr_next;
        input [FIFO_ADDR_WIDTH-1:0] ptr;
        begin
            if (ptr == (FIFO_DEPTH - 1))
                ptr_next = {FIFO_ADDR_WIDTH{1'b0}};
            else
                ptr_next = ptr + {{(FIFO_ADDR_WIDTH-1){1'b0}}, 1'b1};
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
                ADDR_WRITE_COUNT,
                ADDR_TX_COUNT,
                ADDR_TLAST_COUNT:
                    valid_read_addr = 1'b1;
                default:
                    valid_read_addr = 1'b0;
            endcase
        end
    endfunction

    function valid_write_addr;
        input [AXI_ADDR_WIDTH-1:0] addr;
        begin
            case (addr)
                ADDR_CONTROL,
                ADDR_SAMPLE:
                    valid_write_addr = 1'b1;
                default:
                    valid_write_addr = 1'b0;
            endcase
        end
    endfunction

    function [31:0] read_reg;
        input [AXI_ADDR_WIDTH-1:0] addr;
        begin
            case (addr)
                ADDR_CONTROL: read_reg = 32'd0;
                ADDR_STATUS: begin
                    read_reg = 32'd0;
                    read_reg[0] = !fifo_full;
                    read_reg[1] = fifo_empty;
                    read_reg[2] = fifo_full;
                    read_reg[3] = m_axis_tvalid;
                    read_reg[4] = m_axis_tready;
                    read_reg[5] = (error_status != 32'd0);
                    read_reg[15:8] = fifo_count;
                end
                ADDR_ERROR_STATUS: read_reg = error_status;
                ADDR_CONFIG: read_reg = {16'hf1f0, M_AXIS_TDATA_WIDTH[7:0], FIFO_DEPTH[7:0]};
                ADDR_WRITE_COUNT: read_reg = write_count;
                ADDR_TX_COUNT: read_reg = tx_count;
                ADDR_TLAST_COUNT: read_reg = tlast_count;
                default: read_reg = 32'd0;
            endcase
        end
    endfunction

    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            aw_holding <= 1'b0;
            awaddr_reg <= {AXI_ADDR_WIDTH{1'b0}};
            w_holding <= 1'b0;
            wdata_reg <= {AXI_DATA_WIDTH{1'b0}};
            wstrb_reg <= {(AXI_DATA_WIDTH/8){1'b0}};
            bvalid_reg <= 1'b0;
            bresp_reg <= AXI_RESP_OKAY;
            rvalid_reg <= 1'b0;
            rresp_reg <= AXI_RESP_OKAY;
            rdata_reg <= {AXI_DATA_WIDTH{1'b0}};
            wr_ptr <= {FIFO_ADDR_WIDTH{1'b0}};
            rd_ptr <= {FIFO_ADDR_WIDTH{1'b0}};
            fifo_count <= {FIFO_COUNT_WIDTH{1'b0}};
            write_count <= 32'd0;
            tx_count <= 32'd0;
            tlast_count <= 32'd0;
            error_status <= 32'd0;
        end else begin
            if (bvalid_reg && s_axi_bready)
                bvalid_reg <= 1'b0;
            if (rvalid_reg && s_axi_rready)
                rvalid_reg <= 1'b0;

            if (aw_fire) begin
                aw_holding <= 1'b1;
                awaddr_reg <= s_axi_awaddr;
            end
            if (w_fire) begin
                w_holding <= 1'b1;
                wdata_reg <= s_axi_wdata;
                wstrb_reg <= s_axi_wstrb;
            end

            if (do_write) begin
                aw_holding <= 1'b0;
                w_holding <= 1'b0;
                bvalid_reg <= 1'b1;
                bresp_reg <= valid_write_addr(write_addr) ? AXI_RESP_OKAY : AXI_RESP_SLVERR;
                if (!valid_write_addr(write_addr))
                    error_status[1] <= 1'b1;
            end

            if (ar_fire) begin
                rvalid_reg <= 1'b1;
                rresp_reg <= valid_read_addr(s_axi_araddr) ? AXI_RESP_OKAY : AXI_RESP_SLVERR;
                rdata_reg <= valid_read_addr(s_axi_araddr) ? read_reg(s_axi_araddr) : 32'd0;
                if (!valid_read_addr(s_axi_araddr))
                    error_status[2] <= 1'b1;
            end

            if (axis_pop) begin
                rd_ptr <= ptr_next(rd_ptr);
                tx_count <= tx_count + 32'd1;
                if (fifo_last[rd_ptr])
                    tlast_count <= tlast_count + 32'd1;
            end

            if (sample_push_ok) begin
                fifo_data[wr_ptr] <= write_data[M_AXIS_TDATA_WIDTH-1:0];
                fifo_last[wr_ptr] <= write_data[16];
                wr_ptr <= ptr_next(wr_ptr);
                write_count <= write_count + 32'd1;
            end

            case ({sample_push_ok, axis_pop})
                2'b10: fifo_count <= fifo_count + {{(FIFO_COUNT_WIDTH-1){1'b0}}, 1'b1};
                2'b01: fifo_count <= fifo_count - {{(FIFO_COUNT_WIDTH-1){1'b0}}, 1'b1};
                default: fifo_count <= fifo_count;
            endcase

            if (sample_overflow)
                error_status[0] <= 1'b1;

            if (control_clear_errors)
                error_status <= 32'd0;
            if (control_clear_counters) begin
                write_count <= 32'd0;
                tx_count <= 32'd0;
                tlast_count <= 32'd0;
            end
            if (control_soft_reset) begin
                wr_ptr <= {FIFO_ADDR_WIDTH{1'b0}};
                rd_ptr <= {FIFO_ADDR_WIDTH{1'b0}};
                fifo_count <= {FIFO_COUNT_WIDTH{1'b0}};
                write_count <= 32'd0;
                tx_count <= 32'd0;
                tlast_count <= 32'd0;
                error_status <= 32'd0;
            end
        end
    end

endmodule
