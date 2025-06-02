file mkdir out
yosys -import
yosys plugin -i $::env(DIFETTO_SO)
read_liberty -ignore_miss_func -lib $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog -sv out/$::env(TEST)/fixed.v
hierarchy -auto-top
flatten
yosys boundary_scan -test_mode test -clock CK -exclude_io reset
write_verilog -noexpr -noattr out/$::env(TEST)/post_bs.v
synth
dfflibmap -liberty $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
write_verilog -noexpr out/$::env(TEST)/pre_techmap.v
abc -liberty $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
yosys scan_replace -json_mapping $::env(TECH_DIR)/sky130/sky130_mapping.json
write_verilog -noexpr out/$::env(TEST)/nl.v
