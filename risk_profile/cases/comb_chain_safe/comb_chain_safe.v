module top(
    input wire a,
    input wire b,
    input wire c,
    output wire y
);
    wire n1;
    wire n2;

    assign n1 = a & b;
    assign n2 = n1 | c;
    assign y = n2;
endmodule
