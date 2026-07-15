module top (
    input clk,
    input rst_n,
    input din,
    output reg dout
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            dout <= 1'b0;
        else
            dout <= din;
    end
endmodule
