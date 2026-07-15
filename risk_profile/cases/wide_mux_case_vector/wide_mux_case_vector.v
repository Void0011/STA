module top (
    input [2:0] sel,
    input [15:0] a0,
    input [15:0] a1,
    input [15:0] a2,
    input [15:0] a3,
    input [15:0] a4,
    input [15:0] a5,
    input [15:0] a6,
    input [15:0] a7,
    output reg [15:0] y
);
    always @(*) begin
        case (sel)
            3'd0: y = a0;
            3'd1: y = a1;
            3'd2: y = a2;
            3'd3: y = a3;
            3'd4: y = a4;
            3'd5: y = a5;
            3'd6: y = a6;
            default: y = a7;
        endcase
    end
endmodule
