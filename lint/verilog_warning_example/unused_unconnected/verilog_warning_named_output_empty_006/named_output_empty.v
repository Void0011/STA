module child(input a, output out);
  assign out = a;
endmodule
module top(input a);
  child u(.a(a), .out());
endmodule
