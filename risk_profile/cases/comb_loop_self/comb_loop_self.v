module top(
    input wire en,
    output wire y
);
    wire a;

    assign a = a & en;
    assign y = a;
endmodule
