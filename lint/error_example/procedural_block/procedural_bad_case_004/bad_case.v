module top(input [1:0] a, output reg y);
  always @* begin
    case ()
      2'b00: y = 1'b0;
    endcase
  end
endmodule
