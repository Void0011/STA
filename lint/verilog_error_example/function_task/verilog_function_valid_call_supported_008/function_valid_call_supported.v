module top(input a, output y);
  function f;
    input d;
    f = d;
  endfunction
  assign y = f(a);
endmodule
