primitive udp_bad(out, in);
  output out;
  input in;
endprimitive
module top(input a, output y);
  udp_bad u(y, a);
endmodule
