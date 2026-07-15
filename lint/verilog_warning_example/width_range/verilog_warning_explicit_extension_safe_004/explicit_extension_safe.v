`default_nettype none

module top (
    input  wire [3:0] narrow_data,
    output wire [7:0] y
);
    assign y = {4'b0000, narrow_data};
endmodule

`default_nettype wire
