`default_nettype none

module multi_driver (
    input  logic a,
    input  logic b,
    output logic y
);
    assign y = a;

    always_comb begin
        y = b;
    end
endmodule

`default_nettype wire

