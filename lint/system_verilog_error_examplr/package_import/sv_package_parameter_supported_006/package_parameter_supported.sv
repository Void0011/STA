package p;
  parameter int W = 4;
  localparam int L = W;
endpackage
import p::W;
module top(input logic a, output logic y);
  assign y = a;
endmodule
