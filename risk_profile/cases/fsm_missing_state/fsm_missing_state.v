module top(
    input wire clk,
    input wire rst_n,
    input wire start,
    output reg active
);
    localparam IDLE = 2'd0;
    localparam RUN  = 2'd1;
    localparam DONE = 2'd2;

    reg [1:0] state;
    reg [1:0] next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = IDLE;
        active = 1'b0;
        case (state)
            IDLE: next_state = start ? RUN : IDLE;
            RUN: begin
                active = 1'b1;
                next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end
endmodule
