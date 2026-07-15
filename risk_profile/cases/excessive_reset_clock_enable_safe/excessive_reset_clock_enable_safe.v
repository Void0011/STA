module top(input clk, input enable, input [127:0] din, output reg [127:0] dout);
  always @(posedge clk)
    if (enable)
      dout <= din;
endmodule
