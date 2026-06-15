module top(input a, output reg y);
  always @* begin
    y = a;
  end else begin
    y = 1'b0;
  end
endmodule
