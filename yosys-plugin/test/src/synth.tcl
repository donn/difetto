file mkdir out
yosys -import
yosys plugin -i $::env(DIFETTO_SO)
read_liberty -ignore_miss_func -lib $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog -sv spm.v
hierarchy -top spm
flatten
yosys boundary_scan -test_mode test -clock clk -exclude_io rstn -exclude_io sce -exclude_io sci -exclude_io sco
write_verilog -noexpr -noattr out/spm.bs.v
synth -top spm
dfflibmap -liberty $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
write_verilog -noexpr out/spm.pre_techmap.v
abc -liberty $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
yosys scan_replace -json_mapping $::env(TECH_DIR)/sky130/sky130_mapping.json
write_verilog -noexpr out/spm.nl.v
