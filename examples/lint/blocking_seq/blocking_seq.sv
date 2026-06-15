`default_nettype none

module blocking_seq (
    input  logic clk,
    input  logic d,
    output logic q
);
    always_ff @(posedge clk) begin
        q = d;
    end
endmodule

`default_nettype wire

