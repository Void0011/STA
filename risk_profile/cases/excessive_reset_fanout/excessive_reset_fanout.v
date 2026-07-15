module top(input clk, input rst_n, input [7:0] din, output reg [7:0] dout);
  reg [7:0] r0, r1, r2, r3, r4, r5, r6, r7;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      r0 <= 8'b0; r1 <= 8'b0; r2 <= 8'b0; r3 <= 8'b0;
      r4 <= 8'b0; r5 <= 8'b0; r6 <= 8'b0; r7 <= 8'b0;
      dout <= 8'b0;
    end else begin
      r0 <= din; r1 <= r0; r2 <= r1; r3 <= r2;
      r4 <= r3; r5 <= r4; r6 <= r5; r7 <= r6; dout <= r7;
    end
  end
endmodule
