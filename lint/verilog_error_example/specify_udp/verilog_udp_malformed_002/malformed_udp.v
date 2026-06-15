primitive udp_bad(out, in);
  output out;
  input in;
  table
    0 : 0;
endprimitive
module top(input a, output y);
  udp_bad u(y, a);
endmodule
