module top(input clk, input d, output reg q);
    initial q = 1'b0;
    always @(posedge clk) begin
        #1 q <= d;
        $display("q=%b", q);
    end
endmodule
