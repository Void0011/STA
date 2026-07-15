module top(input clk, input en, input [7:0] din, output reg [7:0] dout);
    always @(posedge clk)
        if (en)
            dout <= din;
endmodule
