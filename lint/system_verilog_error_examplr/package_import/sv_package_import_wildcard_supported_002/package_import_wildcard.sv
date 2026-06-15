package p;
  typedef enum logic [0:0] {S0, S1} state_t;
endpackage
import p::*;
module top(input logic a, output logic y);
  state_t state;
  assign y = a;
endmodule
