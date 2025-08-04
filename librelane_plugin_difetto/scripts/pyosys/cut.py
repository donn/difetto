# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
import json
import click

from ys_common import ys


@click.command()
@click.option("--output", type=click.Path(exists=False, dir_okay=False), required=True)
@click.option("--config-in", type=click.Path(exists=True), required=True)
@click.argument("input", nargs=1)
def cut(output, config_in, input):
    with open(config_in, encoding="utf8") as f:
        config = json.load(f)

    d = ys.Design()

    d.run_pass("plugin", "-i", "difetto")

    d.run_pass("read_verilog", input)
    d.run_pass("hierarchy", "-top", config["DESIGN_NAME"])

    dft_top = config["DFT_TOP_MODULE"] or config["DESIGN_NAME"]
    d.run_pass("select", dft_top)

    d.run_pass(
        "sdff_cut",
        "-json_mapping",
        config["DFT_JSON_MAPPING"],
        "-test_mode",
        config["DFT_TEST_MODE_WIRE"],
        "-clock",
        config["DFT_TEST_CLOCK_WIRE"],
    )
    d.run_pass("hierarchy")
    d.run_pass("flatten")
    d.run_pass("write_verilog", output)


if __name__ == "__main__":
    cut()
