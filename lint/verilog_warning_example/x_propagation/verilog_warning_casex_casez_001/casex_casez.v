module top(input [1:0] sel, output reg y);
  always @(*) begin
    y = 1'b0;
    casex (sel)
      2'b0x: y = 1'b1;
      default: y = 1'b0;
    endcase
    casez (sel)
      2'b1?: y = 1'b1;
      2'b0z: y = 1'b0;
      default: y = 1'b0;
    endcase
  end
endmodule
