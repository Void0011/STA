`default_nettype none
`include "defs.vh"

module preprocessor_example (
    input  logic             clk,
    input  logic [`WIDTH-1:0] d,
    output logic [`WIDTH-1:0] q
);
`ifdef USE_FF
    always_ff @(posedge clk) begin
        q <= d;
    end
`else
    assign q = d;
`endif
endmodule

`default_nettype wire

