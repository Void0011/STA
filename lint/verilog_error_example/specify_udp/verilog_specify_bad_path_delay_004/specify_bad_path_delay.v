module top(input a, output y);
  specify
    (a => y) = ;
  endspecify
  assign y = a;
endmodule
