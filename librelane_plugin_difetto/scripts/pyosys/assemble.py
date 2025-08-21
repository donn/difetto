# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
import re
import sys
import json
import bitarray
import click
import yaml
from pathlib import Path

from ys_common import ys

__file_dir__ = Path(__file__).absolute().parent

sys.path.append(str(__file_dir__.parent / "common"))

from chain import load_chains
from patterns import read_patterns_text, write_pattern_bin


@click.command()
@click.option("--tvs-out", type=click.Path(exists=False, dir_okay=False), required=True)
@click.option("--au-out", type=click.Path(exists=False, dir_okay=False), required=True)
@click.option(
    "--mask-out", type=click.Path(exists=False, dir_okay=False), required=True
)
@click.option("--raw-tvs", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option("--raw-au", type=click.Path(exists=True, dir_okay=False), required=True)
@click.option(
    "--chain-yml", type=click.Path(exists=True, dir_okay=False), required=True
)
@click.option("--config-in", type=click.Path(exists=True), required=True)
@click.argument("input", nargs=1)
def assemble(tvs_out, au_out, mask_out, raw_tvs, raw_au, chain_yml, config_in, input):
    with open(config_in, encoding="utf8") as f:
        config = json.load(f)

    with open(chain_yml, encoding="utf8") as f:
        chain_list_raw = yaml.load(f, Loader=yaml.SafeLoader)

    chains = load_chains(chain_list_raw)
    if len(chains) == 0:
        ys.log("No chains found.")
    assert len(chains) == 1, "multiple chains not supported"
    chain = chains[0]
    chain_length = chain.get_length_of_uniform_chain()
    if chain_length == 0:
        ys.log("Chain is empty.")

    d = ys.Design()

    d.run_pass("read_verilog", input)
    d.run_pass("hierarchy", "-top", config["DESIGN_NAME"])

    name_by_tv_location = []
    name_by_au_location = []
    module = d.top_module()
    for name in module.ports:
        wire = module.wires_[name]
        name_str = name.str()
        if name_str.endswith(".d"):  # reg output, in au
            name_by_au_location.append(name_str[1:-2])
        elif name_str.endswith(".q"):  # reg input, in tv
            name_by_tv_location.append(name_str[1:-2])
        else:  # port/boundary scan
            frm = wire.start_offset + wire.width
            to = wire.start_offset
            # if wire.upto: # nl2bench always presumes the msb is first
            #     frm, to = to, frm
            for i in range(frm - 1, to - 1, -1):
                bit_name = name_str[1:] + f"\\[{i}\\]"
                if wire.port_input:
                    name_by_tv_location.append(bit_name)
                elif wire.port_output:
                    name_by_au_location.append(bit_name)

    assembled_location_by_name = {}

    bsr_rx = re.compile(
        r"^(?P<name>[\w]+)\.(?P<io>[io])bsr\/(?P<edge>rising|falling)\.bits\\\[(?P<bit>\d+)\\\]\._store_"
    )
    for loc, instance in enumerate(chain.partitions[0].scan_lists[0].insts):
        name = instance.name
        if bsr_match := bsr_rx.match(instance.name):
            io_name = bsr_match.group("name")
            bit = bsr_match.group("bit")
            name = f"{io_name}\\[{bit}\\]"
        assembled_location_by_name[name] = loc

    tv_assembly_locations = []
    for name in name_by_tv_location:
        loc = assembled_location_by_name[name]
        tv_assembly_locations.append(loc)

    mask = bitarray.bitarray("0" * chain_length, endian="little")
    au_assembly_locations = []
    for name in name_by_au_location:
        loc = assembled_location_by_name[name]
        mask[loc] = 1
        au_assembly_locations.append(loc)

    with open(
        raw_tvs,
        encoding="utf8",
    ) as tv_in_f, open(tvs_out, "wb") as tv_out_f:
        for tv in read_patterns_text(tv_in_f):
            assembled = bitarray.bitarray("0" * chain_length, endian="little")
            for value, location in zip(tv, tv_assembly_locations):
                assembled[location] = value
            write_pattern_bin(tv_out_f, assembled)

    # with open(tvs_out, "rb") as check:
    #     for tv in read_patterns_bin(check):
    #         print(tv)

    with open(
        mask_out,
        "wb",
    ) as mask_out_f:
        write_pattern_bin(mask_out_f, mask)

    with open(
        raw_au,
        encoding="utf8",
    ) as au_in_f, open(au_out, "wb") as au_out_f:
        for au in read_patterns_text(au_in_f):
            assembled = bitarray.bitarray("0" * chain_length, endian="little")
            for value, location in zip(au, au_assembly_locations):
                assembled[location] = value
            write_pattern_bin(au_out_f, assembled)


if __name__ == "__main__":
    assemble()
