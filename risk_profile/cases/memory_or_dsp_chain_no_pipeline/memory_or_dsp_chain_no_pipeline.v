module top (
    input [3:0] addr,
    input [15:0] coeff,
    output reg [31:0] y
);
    reg [15:0] mem [0:15];
    reg [15:0] prod;

    always @(*) begin
        prod = mem[addr] * coeff;
        y = prod + (mem[addr] << 2) + (coeff > 16'd7 ? prod : coeff);
    end
endmodule
