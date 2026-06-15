module long_comb (
    input  wire       clk,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    output reg  [7:0] y
);
    wire [7:0] s0 = (a & b) ^ (c | d);
    wire [7:0] s1 = (s0 + a) ^ (b << 1);
    wire [7:0] s2 = (s1 & c) + (s0 | d);
    wire [7:0] s3 = (s2 ^ s1) + (a & d);

    always @(posedge clk) begin
        y <= s3;
    end
endmodule
