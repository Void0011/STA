module child #(parameter WIDTH=1)(input [WIDTH-1:0] a, output y); assign y = |a; endmodule
module top(input [3:0] a, output y);
  child #(4) u(.a(a), .y(y));
endmodule
