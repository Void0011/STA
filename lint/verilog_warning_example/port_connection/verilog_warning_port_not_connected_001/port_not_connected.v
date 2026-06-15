module child(input a, input b, output y); assign y = a & b; endmodule
module top(input a, output y);
  child u (.a(a), .y(y));
endmodule
