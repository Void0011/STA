module top(input a, output reg y);
  task drive;
    input d;
    begin y = d; end
  endtask
  always @* drive(a);
endmodule
