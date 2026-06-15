`default_nettype none

module implicit_net (
    input  logic a,
    output logic y
);
    assign y = a & typo_signal;
endmodule

`default_nettype wire

