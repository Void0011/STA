module child(output y); assign y = 1'b0; endmodule
module top(output y);
  child u(.y());
  assign y = u.;
endmodule
