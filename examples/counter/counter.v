module counter (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 4'b0000;
        end else begin
            count <= count + 4'b0001;
        end
    end
endmodule
