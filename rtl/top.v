module top (
    input  wire a,
    input  wire b,
    input  wire c,
    output wire y
);
    wire ab;

    assign ab = a & b;
    assign y = ab | c;
endmodule
