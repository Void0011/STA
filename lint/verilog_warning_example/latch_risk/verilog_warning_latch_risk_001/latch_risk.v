module top(input a, input en, output reg y);
  always @* begin
    if (en) y = a;
  end
endmodule
