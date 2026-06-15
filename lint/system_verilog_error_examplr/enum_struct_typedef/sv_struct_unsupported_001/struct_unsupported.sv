module top(input logic a, output logic y);
  typedef struct packed { logic a; logic b; } pair_t;
  assign y = a;
endmodule
