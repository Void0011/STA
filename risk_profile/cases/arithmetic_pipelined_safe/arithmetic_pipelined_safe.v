module top (
    input clk,
    input [15:0] a,
    input [15:0] b,
    input [15:0] c,
    output reg [31:0] y
);
    reg [31:0] prod_stage;

    always @(posedge clk) begin
        prod_stage <= a * b;
        y <= prod_stage + c;
    end
endmodule
