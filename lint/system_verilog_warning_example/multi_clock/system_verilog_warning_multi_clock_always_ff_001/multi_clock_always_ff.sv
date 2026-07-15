module top(input logic clk_a, input logic clk_b, input logic d, output logic q);
  always_ff @(posedge clk_a or posedge clk_b)
    q <= d;
endmodule
