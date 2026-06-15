module output_register (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] d,
    output reg  [7:0] q
);
    always @(posedge clk) begin
        if (!rst_n) begin
            q <= 8'h00;
        end else begin
            q <= d;
        end
    end
endmodule
