module top(input clk, input [31:0] a, input [31:0] b, input [31:0] c, output reg [31:0] y);
    reg [31:0] sum_stage;
    always @(posedge clk) begin
        sum_stage <= a + b;
        y <= sum_stage + c;
    end
endmodule
