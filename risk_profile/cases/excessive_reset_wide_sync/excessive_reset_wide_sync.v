module top(input clk, input rst, input [127:0] din, output reg [127:0] dout);
  always @(posedge clk) begin
    if (rst)
      dout <= 128'b0;
    else
      dout <= din;
  end
endmodule
