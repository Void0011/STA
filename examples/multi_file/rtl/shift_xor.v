module shift_xor (
    input  wire [7:0] x,
    input  wire [7:0] salt,
    output wire [7:0] y
);
    wire [7:0] left_mix = {x[5:0], x[7:6]};
    wire [7:0] right_mix = {salt[1:0], salt[7:2]};

    assign y = (left_mix ^ right_mix) + (x & salt);
endmodule
