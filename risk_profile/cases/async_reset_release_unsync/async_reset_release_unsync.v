module top (
    input clk_a,
    input clk_b,
    input rst_n,
    input d,
    output reg q_a,
    output reg q_b
);
    always @(posedge clk_a or negedge rst_n) begin
        if (!rst_n)
            q_a <= 1'b0;
        else
            q_a <= d;
    end

    always @(posedge clk_b or negedge rst_n) begin
        if (!rst_n)
            q_b <= 1'b0;
        else
            q_b <= q_a;
    end
endmodule
