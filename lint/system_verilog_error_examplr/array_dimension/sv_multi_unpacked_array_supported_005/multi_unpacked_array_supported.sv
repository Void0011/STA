module top(input logic a, output logic y);
  logic [7:0] mem [0:3][0:1];
  assign y = a;
endmodule
