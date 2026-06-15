interface bus_if;
  logic data;
  modport master(output data);
endinterface
module top;
  bus_if.master bus();
endmodule
