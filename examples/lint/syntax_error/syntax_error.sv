`default_nettype none

module syntax_error (
    input  logic a,
    input  logic b,
    output logic y
);
    assign y = a & ;
endmodule

`default_nettype wire

