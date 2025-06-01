yosys -import
plugin -i $::env(DIFETTO_SO)
read_liberty -ignore_miss_func -lib $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog -sv ./out/spm.nl.v
hierarchy -top spm
select spm
yosys sdff_cut -json_mapping $::env(TECH_DIR)/sky130/sky130_mapping.json -test_mode test -clock clk -exclude_io rstn -exclude_io sce -exclude_io sci -exclude_io sco
techmap -map $::env(TECH_DIR)/sky130/unmap_mux.v.map
write_verilog -selected -noexpr ./out/spm.cut.pre_opt.v
opt_clean -purge
abc -liberty $::env(TECH_DIR)/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
write_verilog -selected -noexpr ./out/spm.cut.v
