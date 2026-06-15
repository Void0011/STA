`default_nettype none

module latch_risk (
    input  logic en,
    input  logic d,
    output logic q
);
    always_comb begin
        if (en) begin
            q = d;
        end
    end
endmodule

`default_nettype wire

