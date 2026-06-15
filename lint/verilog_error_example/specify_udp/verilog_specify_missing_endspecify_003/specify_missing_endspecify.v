module top(input a, output y);
  specify
    (a => y) = 1;
  assign y = a;
endmodule
