`default_nettype none
module top(input a, output y);
  assign y = a & missing_sig;
endmodule
`default_nettype wire
