module top(input logic a, output logic y);
  always_comb begin
    assert (a);
    y = a;
  end
endmodule
