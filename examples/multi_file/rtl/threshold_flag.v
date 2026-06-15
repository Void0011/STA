module threshold_flag (
    input  wire [7:0] value,
    output wire       flag
);
    assign flag = (value[7:4] > 4'h9) | (&value[3:0]);
endmodule
