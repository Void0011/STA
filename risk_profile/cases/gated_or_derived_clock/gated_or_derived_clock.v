module top (
    input clk,
    input enable,
    input d,
    output reg q
);
    wire gated_clk;

    assign gated_clk = clk & enable;

    always @(posedge gated_clk) begin
        q <= d;
    end
endmodule
