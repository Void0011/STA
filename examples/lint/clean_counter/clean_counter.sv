`default_nettype none

module clean_counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       en,
    output logic [3:0] count
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 4'd0;
        end else if (en) begin
            count <= count + 4'd
        end
    end
endmodule

`default_nettype wire

