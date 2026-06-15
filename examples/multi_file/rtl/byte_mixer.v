module byte_mixer (
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    output wire [7:0] y
);
    wire [7:0] ab = a & b;
    wire [7:0] ac = a | c;
    wire [7:0] bc = b ^ c;

    assign y = (ab ^ ac) + {bc[6:0], bc[7]};
endmodule
