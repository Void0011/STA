module top(input logic a, input logic en, output logic y);
  always_comb begin
    if (en) y = a;
  end
endmodule
