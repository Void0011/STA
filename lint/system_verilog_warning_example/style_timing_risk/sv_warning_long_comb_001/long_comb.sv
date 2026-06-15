module top(input logic [7:0] a, b, c, d, output logic [7:0] y);
  always_comb begin
    y = (((a + b) ^ (c + d)) + ((a & b) | (c & d))) ^ ((a << 1) + (b >> 1));
  end
endmodule
