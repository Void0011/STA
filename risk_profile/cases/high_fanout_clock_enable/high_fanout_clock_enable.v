module top(input clk, input en, input [127:0] din, output reg [127:0] dout);
    always @(posedge clk)
        if (en)
            dout <= din;
endmodule
