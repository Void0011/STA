module top(
    input wire sel,
    input wire in,
    output wire y
);
    wire a;
    wire b;

    assign a = sel ? b : in;
    assign b = a;
    assign y = b;
endmodule
