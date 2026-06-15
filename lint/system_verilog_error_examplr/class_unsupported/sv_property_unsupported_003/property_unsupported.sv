module top(input logic clk, output logic y);
  property p; @(posedge clk) 1'b1; endproperty
  assign y = 1'b0;
endmodule
