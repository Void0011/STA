module top (
    input clk,
    input enable,
    input [5:0] d,
    output reg [5:0] q
);
    always @(posedge clk) begin
        if (enable) q[0] <= d[0];
    end

    always @(posedge clk) begin
        if (enable) q[1] <= d[1];
    end

    always @(posedge clk) begin
        if (enable) q[2] <= d[2];
    end

    always @(posedge clk) begin
        if (enable) q[3] <= d[3];
    end

    always @(posedge clk) begin
        if (enable) q[4] <= d[4];
    end

    always @(posedge clk) begin
        if (enable) q[5] <= d[5];
    end
endmodule
