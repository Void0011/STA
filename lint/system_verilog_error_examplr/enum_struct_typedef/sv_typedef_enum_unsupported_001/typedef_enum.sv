module top(input logic a, output logic y);
  typedef enum logic [1:0] {IDLE, RUN} state_t;
  assign y = a;
endmodule
