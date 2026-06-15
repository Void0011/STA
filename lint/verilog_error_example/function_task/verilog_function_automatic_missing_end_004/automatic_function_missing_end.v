module top(input a, output y);
  function automatic f;
    input a;
    f = a;
  assign y = f(a);
endmodule
