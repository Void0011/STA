`default_nettype none

interface unsupported_bus;
    logic data;
endinterface

class unsupported_class;
    int value;
endclass

module unsupported_top (
    input logic clk
);
endmodule

`default_nettype wire
