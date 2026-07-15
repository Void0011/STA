module top (
    input clk,
    input start,
    input [7:0] a,
    input [7:0] b,
    output reg [15:0] y
);
    reg [1:0] slow_count;

    always @(posedge clk) begin
        if (start)
            slow_count <= 2'd0;
        else if (slow_count != 2'd3)
            slow_count <= slow_count + 1'b1;

        if (slow_count == 2'd3)
            y <= a * b;
    end
endmodule
