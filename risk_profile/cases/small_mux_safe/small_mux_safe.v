module top (
    input sel,
    input [7:0] a,
    input [7:0] b,
    output reg [7:0] y
);
    always @(*) begin
        if (sel) y = a;
        else y = b;
    end
endmodule
