`timescale 1ns/1ps
module top(input a, output y);
  child u(.a(a), .y(y));
endmodule
