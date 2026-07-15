module top(
  input signed [7:0] signed_a,
  input signed [7:0] signed_b,
  input [7:0] unsigned_a,
  output reg signed [7:0] out_signed,
  output reg [7:0] out_unsigned
);
  always @(*) begin
    out_signed = signed_a + signed_b;
    out_unsigned = $unsigned(signed_a);
    if ($signed(unsigned_a) < signed_b)
      out_signed = $signed(unsigned_a);
  end
endmodule
