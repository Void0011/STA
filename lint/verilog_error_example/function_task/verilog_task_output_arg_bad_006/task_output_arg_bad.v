module top(input a, output reg y);
  task drive;
    output;
    y = a;
  endtask
  always @* drive(y);
endmodule
