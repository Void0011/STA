`default_nettype none

module gated_clock (
    input  logic clk,
    input  logic en,
    input  logic d,
    output logic q
);
    logic gated_clk;

    assign gated_clk = clk & en;

    always_ff @(posedge gated_clk) begin
        q <= d;
    end
endmodule

`default_nettype wire

