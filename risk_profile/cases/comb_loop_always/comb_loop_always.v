module top(
    input wire in,
    output wire y
);
    reg a;
    reg b;

    always @(*) begin
        a = b;
        b = a ^ in;
    end

    assign y = a;
endmodule
