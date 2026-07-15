module top #(parameter WIDTH = 8, parameter USE_XOR = 1) (
    input [WIDTH-1:0] a,
    input [WIDTH-1:0] b,
    output [WIDTH-1:0] y
);
    genvar index;
    generate
        for (index = 0; index < WIDTH; index = index + 1) begin : g_bit
            if (USE_XOR) begin : g_xor
                assign y[index] = a[index] ^ b[index];
            end else begin : g_or
                assign y[index] = a[index] | b[index];
            end
        end
    endgenerate
endmodule
