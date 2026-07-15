`default_nettype none

module top (
    input  wire [15:0] wide_data,
    output reg  [7:0]  y
);
    always @* begin
        y = wide_data;
    end
endmodule

`default_nettype wire
