module child(input logic [3:0] a, output logic y); assign y = |a; endmodule
module top(input logic a, output logic y);
  child u(.a(a), .y(y));
endmodule
