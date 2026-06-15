module top(input a, output y);
  generate
    if (1) begin : g
      assign y = a;
    end
endmodule
