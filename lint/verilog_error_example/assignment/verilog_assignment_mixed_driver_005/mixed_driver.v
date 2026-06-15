module top(input clk, input d, output reg q);
  assign q = d;
  always @(posedge clk) q <= d;
endmodule
