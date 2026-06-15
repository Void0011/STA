`default_nettype none

module long_comb (
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic [7:0] c,
    input  logic [7:0] d,
    output logic [7:0] y
);
    always_comb begin
        y = (((a + b) ^ (c - d)) & ((a << 1) | (b >> 1)))
          + ((a & c) ^ (b | d))
          + ((a == b) ? c : d);
    end
endmodule

`default_nettype wire

