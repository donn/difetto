yosys -import
plugin -i $::env(DIFETTO_SO)
read_liberty -ignore_miss_func -lib $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog -sv ./out/$::env(TEST)/nl.v
hierarchy -auto-top
yosys sdff_cut -json_mapping $::env(TECH_DIR)/sky130/sky130_mapping.json -test_mode test -clock CK -exclude_io reset
techmap -map $::env(TECH_DIR)/sky130/unmap_muxi.v.map
techmap -map $::env(TECH_DIR)/sky130/unmap_mux.v.map
write_verilog -selected -noexpr ./out/$::env(TEST)/cut_pre_opt.v
opt_clean -purge
abc -liberty $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
write_verilog -selected -noexpr ./out/$::env(TEST)/cut.v
