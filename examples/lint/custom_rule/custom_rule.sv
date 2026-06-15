`default_nettype none

module custom_rule (
    input  logic clk,
    input  logic d,
    output logic q
);
    logic tmp_stage;

    always_ff @(posedge clk) begin
        tmp_stage <= d;
        q <= tmp_stage;
    end
endmodule

`default_nettype wire

