`default_nettype none

module nonblocking_comb (
    input  logic a,
    input  logic b,
    output logic y
);
    always_comb begin
        y <= a & b;
    end
endmodule

`default_nettype wire

