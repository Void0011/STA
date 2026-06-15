module top(input a, output reg y);
  task drive;
    input a;
    y = a;
  always @* drive(a);
endmodule
