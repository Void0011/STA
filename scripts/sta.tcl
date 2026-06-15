read_liberty lib/example.lib
read_verilog build/top_mapped.v
link_design top

create_clock -name vclk -period 1.000
set_input_delay -clock vclk 0.050 [all_inputs]
set_output_delay -clock vclk 0.050 [all_outputs]
set_driving_cell -lib_cell BUF_X1 [all_inputs]
set_load 0.030 [all_outputs]

report_checks -from [all_inputs] -to [all_outputs] -path_delay max -fields {slew cap input nets fanout} -digits 4
report_checks -from [all_inputs] -to [all_outputs] -path_delay min -fields {slew cap input nets fanout} -digits 4
report_tns
report_wns
