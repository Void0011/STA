module top (
    input clk_a,
    input clk_b,
    input pulse_in,
    output reg pulse_seen
);
    reg pulse_a;

    always @(posedge clk_a) begin
        pulse_a <= pulse_in;
    end

    always @(posedge clk_b) begin
        pulse_seen <= pulse_a;
    end
endmodule
