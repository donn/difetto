# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
import json
import re
import click
import yaml

import re

from ys_common import ys


@click.command()
@click.option("--output", type=click.Path(exists=False, dir_okay=False), required=True)
@click.option(
    "--chain-out", type=click.Path(exists=False, dir_okay=False), required=True
)
@click.option("--config-in", type=click.Path(exists=True), required=True)
@click.argument("input", nargs=1)
def scan_replace(output, chain_out, config_in, input):
    with open(config_in, encoding="utf8") as f:
        config = json.load(f)

    d = ys.Design()

    d.run_pass("plugin", "-i", "difetto")

    d.run_pass("read_verilog", input)
    dft_top = config["DFT_TOP_MODULE"] or config["DESIGN_NAME"]
    d.run_pass("hierarchy", "-top", dft_top)

    d.run_pass("setattr", "-mod", "-unset", "keep_hierarchy")
    d.run_pass("flatten")

    module = d.module(f"\\{dft_top}")
    src = module.wire(f"\\{config['DFT_SCAN_IN_PATTERN']}")
    sink = module.wire(f"\\{config['DFT_SCAN_OUT_PATTERN']}")
    en = module.wire(f"\\{config['DFT_SCAN_ENABLE_PATTERN']}")

    with open(config["DFT_JSON_MAPPING"]) as f:
        scannable_modules = [f"\\{name}" for name in json.load(f)["mapping"].values()]

    def_escape_characters = re.compile(r"(\[|\])")
    insts = []
    last = src
    counter = 0
    for _, cell in module.cells_.items():
        if cell.type in scannable_modules:
            print(cell.name)
            insts.append(def_escape_characters.sub(r"\\\1", cell.name.str()[1:]))
            cell.setPort("\\SCD", ys.SigSpec(last))
            cell.setPort("\\SCE", ys.SigSpec(en))
            last = cell.getPort("\\Q")
            counter += 1
    module.connect(ys.SigSpec(sink), ys.SigSpec(last))

    with open(chain_out, "w", encoding="utf8") as f:
        yaml.safe_dump(
            [
                {
                    "name": "chain_0",
                    "partitions": [
                        {"name": "default", "scan_lists": [{"insts": insts}]}
                    ],
                }
            ],
            f,
        )

    d.run_pass("splitnets")
    d.run_pass("opt_clean", "-purge")
    d.run_pass(
        "write_verilog",
        "-noexpr",
        "-nohex",
        "-nodec",
        "-defparam",
        output,
    )


if __name__ == "__main__":
    scan_replace()
