module top (
    input a,
    input b,
    input sel,
    output reg y
);
    always @(*) begin
        if (sel)
            y = a & b;
    end
endmodule
