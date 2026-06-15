module top(input logic [1:0] a, output logic y);
  always_comb begin
    unique case (a)
      2'b00: y = 1'b0;
    endcase
  end
endmodule
