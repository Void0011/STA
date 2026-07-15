module top(
    input wire in,
    output wire y
);
    wire a;
    wire b;

    assign a = b;
    assign b = a | in;
    assign y = a;
endmodule
