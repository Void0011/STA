package p;
  parameter int W = 1;
endpackage
import p::*;
module top(input logic a, output logic y);
  assign y = a;
endmodule
