module latch_example (
    input  wire en,
    input  wire d,
    output reg  q
);
    always @* begin
        if (en) begin
            q = d;
        end
    end
endmodule
