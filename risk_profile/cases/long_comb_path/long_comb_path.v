module top (
    input [15:0] a,
    input [15:0] b,
    input [15:0] c,
    input [15:0] d,
    input [15:0] e,
    input [15:0] f,
    input [15:0] g,
    input [15:0] h,
    input [15:0] i,
    input [15:0] j,
    input [15:0] k,
    input [15:0] l,
    output [15:0] y
);
    assign y = (((a + b) ^ (c - d)) + ((e & f) | (g ^ h))) +
               ((i > j) ? (k << 1) : (l >> 1));
endmodule
