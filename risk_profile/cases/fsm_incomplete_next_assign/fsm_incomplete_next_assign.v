module top(
    input wire clk,
    input wire rst_n,
    input wire start,
    output reg active
);
    localparam IDLE = 1'b0;
    localparam RUN  = 1'b1;

    reg state;
    reg next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        active = 1'b0;
        case (state)
            IDLE: begin
                if (start)
                    next_state = RUN;
            end
            RUN: begin
                active = 1'b1;
                next_state = IDLE;
            end
        endcase
    end
endmodule
