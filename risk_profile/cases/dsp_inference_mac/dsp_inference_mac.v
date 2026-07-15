module top(input [15:0] a, input [15:0] b, input [31:0] c, output [31:0] y);
    assign y = a * b + c;
endmodule
