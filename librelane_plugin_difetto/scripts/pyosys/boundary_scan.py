# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
import json
import os
import shlex
import click

from ys_common import ys


@click.command()
@click.option("--output", type=click.Path(exists=False, dir_okay=False), required=True)
@click.option("--config-in", type=click.Path(exists=True), required=True)
@click.argument("input", nargs=1)
def boundary_scan(output, config_in, input):
    with open(config_in, encoding="utf8") as f:
        config = json.load(f)

    d = ys.Design()

    d.run_pass("plugin", "-i", "difetto")

    d.run_pass("read_verilog", input)
    d.run_pass("hierarchy", "-top", config["DESIGN_NAME"])

    dft_top = config["DFT_TOP_MODULE"] or config["DESIGN_NAME"]
    d.run_pass("select", dft_top)

    exclude_io_args = []
    if exclude_ios := config["DFT_BSCAN_EXCLUDE_IO"]:
        for io in exclude_ios:
            exclude_io_args.append("-exclude_io")
            exclude_io_args.append(io)

    d.run_pass(
        "boundary_scan",
        "-test_mode",
        config["DFT_TEST_MODE_WIRE"],
        "-clock",
        config["DFT_TEST_CLOCK_WIRE"],
        *exclude_io_args,
    )

    dfflibmap_args = []
    for lib in shlex.split(os.environ["_libs_synth"]):
        dfflibmap_args.extend(["-liberty", lib])
    d.run_pass("dfflibmap", *dfflibmap_args)

    d.run_pass("write_verilog", output)


if __name__ == "__main__":
    boundary_scan()
