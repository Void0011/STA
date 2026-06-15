module top(input [1:0] a, output [1:0] y);
  genvar i;
  generate
    for (i=0; i<2; i=i+1) begin : g
      assign y[i] = a[i];
    end
  endgenerate
endmodule
