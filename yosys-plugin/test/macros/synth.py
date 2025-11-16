from common import ys, lib, mapping, __file_dir__, signal_flags

d = ys.Design()
ys.run_pass(f"read_verilog {__file_dir__}/macro.v", d)
ys.run_pass(f"read_verilog {__file_dir__}/top.v", d)
ys.run_pass(f"hierarchy -auto-top", d)
ys.run_pass("boundary_scan " + signal_flags, d)
ys.run_pass("write_verilog -noexpr -noattr top.after_bs.v", d)
ys.run_pass("synth", d)
ys.run_pass(f"dfflibmap -liberty {lib}", d)
ys.run_pass("write_verilog -noexpr top.pre_techmap.v", d)
ys.run_pass(f"abc -liberty {lib}", d)
ys.run_pass(f"scan_replace -json_mapping {mapping}", d)
ys.run_pass("write_verilog top.nl.v", d)
