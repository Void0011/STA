module top (
    input [15:0] a,
    input [15:0] b,
    input [15:0] c,
    input [15:0] d,
    input [15:0] e,
    output [31:0] y
);
    assign y = (a * b) + (c * d) + e + ((a > c) ? d : b);
endmodule
