module top (
    input clk_a,
    input clk_b,
    input [7:0] data_in,
    output reg [7:0] data_seen
);
    reg [7:0] data_a;

    always @(posedge clk_a) begin
        data_a <= data_in;
    end

    always @(posedge clk_b) begin
        data_seen <= data_a;
    end
endmodule
