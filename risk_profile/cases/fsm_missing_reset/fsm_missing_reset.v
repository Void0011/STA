module top(
    input wire clk,
    input wire start,
    output reg active
);
    localparam IDLE = 1'b0;
    localparam RUN  = 1'b1;

    reg state;
    reg next_state;

    always @(posedge clk) begin
        state <= next_state;
    end

    always @(*) begin
        next_state = IDLE;
        active = 1'b0;
        case (state)
            IDLE: next_state = start ? RUN : IDLE;
            RUN: begin
                active = 1'b1;
                next_state = RUN;
            end
            default: next_state = IDLE;
        endcase
    end
endmodule
