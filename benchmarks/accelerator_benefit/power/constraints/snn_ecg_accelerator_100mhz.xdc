create_clock -name core_clk_100mhz -period 10.000 -waveform {0 5} [get_ports clk]
set_input_delay 0.500 -clock core_clk_100mhz [get_ports {rst start sample_valid adc_data[*]}]
set_output_delay 0.500 -clock core_clk_100mhz [all_outputs]
