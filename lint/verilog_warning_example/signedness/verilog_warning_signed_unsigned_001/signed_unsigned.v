module top(
  input signed [7:0] signed_a,
  input [7:0] unsigned_b,
  input signed [3:0] signed_small,
  input choose,
  output reg signed [7:0] out_signed,
  output reg [7:0] out_unsigned
);
  always @(*) begin
    out_signed = signed_a + unsigned_b;
    out_unsigned = signed_small;
    if (signed_a < unsigned_b)
      out_unsigned = signed_a >>> unsigned_b[2:0];
    else
      out_unsigned = choose ? signed_a : unsigned_b;
  end
endmodule
