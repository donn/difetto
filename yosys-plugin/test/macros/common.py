from pathlib import Path

import libyosys as ys

__file_dir__= Path(__file__).absolute().parent

difetto = __file_dir__.parents[1] / "difetto.so"
tech = __file_dir__.parent / "tech" / "sky130"
lib = next(tech.glob("*.lib"))
mapping = next(tech.glob("*_mapping.json"))
signal_flags = (
    "-clock clk "
    "-test_mode tm "
    "-exclude_io clk "
    "-exclude_io tm "
    "-exclude_io !rstn "
    "-exclude_io si "
    "-exclude_io se "
    "-exclude_io so "
    "-macro lower "
    "-exclude_io lower/clk "
    "-exclude_io lower/tm "
    "-exclude_io !lower/rstn "
    "-exclude_io lower/si "
    "-exclude_io lower/se "
    "-exclude_io lower/so "
    "-macro higher0 "
    "-exclude_io higher0/clk "
    "-exclude_io higher0/tm "
    "-exclude_io !higher0/rstn "
    "-exclude_io higher0/si "
    "-exclude_io higher0/se "
    "-exclude_io higher0/so "
    "-macro higher1 "
    "-exclude_io higher1/clk "
    "-exclude_io higher1/tm "
    "-exclude_io !higher1/rstn "
    "-exclude_io higher1/si "
    "-exclude_io higher1/se "
    "-exclude_io higher1/so "
)
ys.run_pass(f"plugin -i {difetto}")
