module top(input clk, input we, input [7:0] addr, input [15:0] din, output [15:0] dout);
    reg [15:0] mem [0:255];
    always @(posedge clk)
        if (we)
            mem[addr] <= din;
    assign dout = mem[addr];
endmodule
