module top(input clk, input [15:0] din, output reg [15:0] dout);
    reg [15:0] data_reg;
    always @(posedge clk) begin
        data_reg <= din;
        dout <= data_reg;
    end
endmodule
