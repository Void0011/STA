module top(input [7:0] a, output [3:0] y);
  assign y = a[:3];
endmodule
