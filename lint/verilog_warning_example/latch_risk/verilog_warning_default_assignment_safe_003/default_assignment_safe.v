`default_nettype none

module top (
    input  wire [1:0] sel,
    input  wire       a,
    input  wire       b,
    output reg        y
);
    always @* begin
        y = 1'b0;
        case (sel)
            2'd0: y = a;
            2'd1: y = b;
            default: y = 1'b0;
        endcase
    end
endmodule

`default_nettype wire
