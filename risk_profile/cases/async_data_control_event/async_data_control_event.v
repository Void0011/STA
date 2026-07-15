module top(input clk, input async_req, input d, output reg q);
    always @(posedge clk or posedge async_req)
        if (async_req)
            q <= 1'b1;
        else
            q <= d;
endmodule
