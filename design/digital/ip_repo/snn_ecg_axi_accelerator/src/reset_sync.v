`timescale 1ns / 1ps

module reset_sync(
    input wire clk,
    input wire arstn,
    output wire rst
);

    (* ASYNC_REG = "TRUE" *) reg [2:0] sync_reg;

    always @(posedge clk or negedge arstn) begin
        if (!arstn)
            sync_reg <= 3'b000;
        else
            sync_reg <= {sync_reg[1:0], 1'b1};
    end

    assign rst = ~sync_reg[2];

endmodule
