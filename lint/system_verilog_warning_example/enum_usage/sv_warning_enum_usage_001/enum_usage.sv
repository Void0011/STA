module top(input logic a, output logic y);
  typedef enum logic [0:0] {S0, S1} state_t;
  state_t state;
  assign y = a;
endmodule
