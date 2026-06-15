module child(input a, output y); assign y = a; endmodule
module top(input a, output y);
  child (.a(a), .y(y));
endmodule
