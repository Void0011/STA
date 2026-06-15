module multi_top (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    output wire [7:0] y,
    output wire       flag
);
    wire [7:0] a_q;
    wire [7:0] b_q;
    wire [7:0] c_q;
    wire [7:0] d_q;
    wire [7:0] mix0;
    wire [7:0] mix1;
    wire [7:0] acc;
    wire [7:0] next_y;
    wire       cmp_flag;

    input_register u_input_a (
        .clk(clk),
        .rst_n(rst_n),
        .d(a),
        .q(a_q)
    );

    input_register u_input_b (
        .clk(clk),
        .rst_n(rst_n),
        .d(b),
        .q(b_q)
    );

    input_register u_input_c (
        .clk(clk),
        .rst_n(rst_n),
        .d(c),
        .q(c_q)
    );

    input_register u_input_d (
        .clk(clk),
        .rst_n(rst_n),
        .d(d),
        .q(d_q)
    );

    byte_mixer u_byte_mixer (
        .a(a_q),
        .b(b_q),
        .c(c_q),
        .y(mix0)
    );

    shift_xor u_shift_xor (
        .x(mix0),
        .salt(d_q),
        .y(mix1)
    );

    small_accumulator u_small_accumulator (
        .x(mix1),
        .y(acc)
    );

    result_select u_result_select (
        .sel(c_q[0]),
        .a(acc),
        .b(mix0 ^ d_q),
        .y(next_y)
    );

    threshold_flag u_threshold_flag (
        .value(next_y),
        .flag(cmp_flag)
    );

    output_register u_output_register (
        .clk(clk),
        .rst_n(rst_n),
        .d(next_y),
        .q(y)
    );

    flag_register u_flag_register (
        .clk(clk),
        .rst_n(rst_n),
        .d(cmp_flag),
        .q(flag)
    );
endmodule
