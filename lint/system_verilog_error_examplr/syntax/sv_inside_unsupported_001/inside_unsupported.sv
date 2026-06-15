module top(input logic [1:0] a, output logic y);
  assign y = a inside {2'b00, 2'b11};
endmodule
