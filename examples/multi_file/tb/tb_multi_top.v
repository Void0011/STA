`timescale 1ns/1ps

module tb_multi_top;
    reg        clk;
    reg        rst_n;
    reg  [7:0] a;
    reg  [7:0] b;
    reg  [7:0] c;
    reg  [7:0] d;
    wire [7:0] y;
    wire       flag;

    multi_top dut (
        .clk(clk),
        .rst_n(rst_n),
        .a(a),
        .b(b),
        .c(c),
        .d(d),
        .y(y),
        .flag(flag)
    );

    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    initial begin
        rst_n = 1'b0;
        a = 8'h12;
        b = 8'h34;
        c = 8'h56;
        d = 8'h78;
        #20;
        rst_n = 1'b1;
        #10;
        a = 8'ha5;
        b = 8'h3c;
        c = 8'h0f;
        d = 8'hc3;
        #30;
        $finish;
    end
endmodule
