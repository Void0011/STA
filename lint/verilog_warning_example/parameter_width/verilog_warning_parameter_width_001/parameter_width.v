module top #(parameter WIDTH = 0) (
    input [WIDTH-1:0] a,
    output [WIDTH-1:0] y
);
    assign y = a;
endmodule
