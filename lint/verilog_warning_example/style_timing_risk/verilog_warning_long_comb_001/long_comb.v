module top(input [7:0] a, b, c, d, output [7:0] y);
  assign y = (((a + b) ^ (c + d)) + ((a & b) | (c & d))) ^ ((a << 1) + (b >> 1));
endmodule
