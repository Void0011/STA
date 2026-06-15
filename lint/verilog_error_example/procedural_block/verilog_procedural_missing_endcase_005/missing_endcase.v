module top(input [1:0] a, output reg y);
  always @* begin
    case (a)
      2'b00: y = 1'b0;
  end
endmodule
