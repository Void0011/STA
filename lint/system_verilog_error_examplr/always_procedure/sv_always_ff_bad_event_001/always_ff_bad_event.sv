module top(input logic clk, input logic d, output logic q);
  always_ff @(posedge) q <= d;
endmodule
