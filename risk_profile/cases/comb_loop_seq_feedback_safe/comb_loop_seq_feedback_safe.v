module top(
    input wire clk,
    input wire d,
    output wire y
);
    reg q;

    always @(posedge clk) begin
        q <= q ^ d;
    end

    assign y = q;
endmodule
