from common import ys, lib, mapping, __file_dir__, signal_flags

d = ys.Design()
ys.run_pass(f"read_verilog {__file_dir__}/macro.v", d)
ys.run_pass(f"read_liberty -ignore_miss_func -lib {lib}", d)
ys.run_pass(f"read_verilog top.nl.v", d)
ys.run_pass(f"hierarchy -auto-top", d)
ys.run_pass(f"select top", d)
ys.run_pass(f"sdff_cut -json_mapping {mapping} " + signal_flags, d)
ys.run_pass(f"write_verilog top.cut.pre_opt.v", d)
ys.run_pass(f"opt_clean -purge", d)
ys.run_pass(f"hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO", d)
ys.run_pass(f"write_verilog -selected -noexpr top.cut.v", d)


