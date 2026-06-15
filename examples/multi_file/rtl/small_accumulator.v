module small_accumulator (
    input  wire [7:0] x,
    output wire [7:0] y
);
    wire [3:0] lo = x[3:0] + x[7:4];
    wire [3:0] hi = (x[7:4] ^ x[3:0]) + {3'b000, x[0]};

    assign y = {hi, lo} + {x[0], x[7:1]};
endmodule
