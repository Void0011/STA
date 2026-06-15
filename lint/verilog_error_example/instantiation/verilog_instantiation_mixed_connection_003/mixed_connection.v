module child(input a, input b, output y); assign y = a & b; endmodule
module top(input a, input b, output y);
  child u (.a(a), b, .y(y));
endmodule
