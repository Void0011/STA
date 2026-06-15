module top(input logic clk, output logic y);
  covergroup cg @(posedge clk); endgroup
  assign y = 1'b0;
endmodule
