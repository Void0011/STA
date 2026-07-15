module top(input clk_a, input clk_b, input rst_n, input d, output reg q0, output reg q1, output reg q2);
  always @(posedge clk_a or posedge clk_b)
    q0 <= d;

  always @(posedge clk_a or negedge clk_b)
    q1 <= d;

  always @(posedge clk_a or negedge rst_n)
    if (!rst_n)
      q2 <= 1'b0;
    else
      q2 <= d;
endmodule
