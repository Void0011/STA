module top(input logic [3:0] a, output logic y);
  logic signed [7:0] mem [0:3];
  assign y = a[0];
endmodule
