module top(input [1:0] sel, output reg y);
  always @(*) begin
    y = 1'b0;
    case (sel)
      2'b00: y = 1'b1;
      default: y = 1'b0;
    endcase
    if ((sel & 2'b10) == 2'b10)
      y = 1'b1;
  end
endmodule
