module top(input [31:0] a, input [31:0] b, input [31:0] c, input [31:0] d, output [31:0] y);
    assign y = (a > b) ? ((a > c) ? a + d : c - b) : ((b > d) ? b + c : d - a);
endmodule
