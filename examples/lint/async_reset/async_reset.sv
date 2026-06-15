`default_nettype none

module async_reset (
    input  logic clk_a,
    input  logic clk_b,
    input  logic rst_n,
    input  logic d,
    output logic qa,
    output logic qb
);
    always_ff @(posedge clk_a or negedge rst_n) begin
        if (!rst_n) begin
            qa <= 1'b0;
        end else begin
            qa <= d;
        end
    end

    always_ff @(posedge clk_b or negedge rst_n) begin
        if (!rst_n) begin
            qb <= 1'b0;
        end else begin
            qb <= d;
        end
    end
endmodule

`default_nettype wire

