module top(
    input logic in,
    output logic y
);
    logic a;
    logic b;

    always_comb begin
        a = b;
        b = a | in;
    end

    assign y = a;
endmodule
