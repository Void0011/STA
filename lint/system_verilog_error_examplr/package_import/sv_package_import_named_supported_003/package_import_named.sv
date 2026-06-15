package p;
  typedef enum logic [0:0] {S0, S1} state_t;
endpackage
import p::state_t;
module top(input logic a, output logic y);
  state_t state;
  assign y = a;
endmodule
