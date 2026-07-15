module top (
    input [2:0] sel,
    input [7:0] a,
    input [7:0] b,
    input [7:0] c,
    input [7:0] d,
    input [7:0] e,
    input [7:0] f,
    input [7:0] g,
    output reg [7:0] y
);
    always @(*) begin
        y = 8'h00;
        if (sel == 3'd0) y = a;
        else if (sel == 3'd1) y = b;
        else if (sel == 3'd2) y = c;
        else if (sel == 3'd3) y = d;
        else if (sel == 3'd4) y = e;
        else if (sel == 3'd5) y = f;
        else y = g;
    end
endmodule
