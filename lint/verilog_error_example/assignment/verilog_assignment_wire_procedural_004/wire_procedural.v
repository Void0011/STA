module top(input clk, input d, output y);
  always @(posedge clk) begin
    y <= d;
  end
endmodule
