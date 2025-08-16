import json
import os
import random

# with this one statement i've unleashed a whole bunch of interdependency BS
import yaml

import cocotb
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject
from cocotb.triggers import RisingEdge
from cocotb.runner import get_runner
from cocotb.binary import BinaryValue


@cocotb.test()
async def chain_test(dut: HierarchyObject):
    """Test that the chain is valid"""

    config_json = os.environ["STEP_CONFIG"]
    chain_yml = os.environ["CURRENT_CHAIN_YML"]

    with open(config_json, encoding="utf8") as f:
        config = json.load(f)

    with open(chain_yml, encoding="utf8") as f:
        chain_dict = yaml.load(f, Loader=yaml.SafeLoader)

    if len(chain_dict) == 0:
        cocotb.log("No chains found.")
        return
    assert len(chain_dict) == 1, "multiple chains not supported"
    chain = chain_dict[0]
    partitions = chain["partitions"]
    if len(partitions) == 0:
        cocotb.log("Chain lacks partitions.")
        return
    assert len(partitions) == 1, "multiple partitions not supported"
    partition = partitions[0]
    scan_lists = partition["scan_lists"]
    if len(scan_lists) == 0:
        cocotb.log("Partition lacks scan_lists.")
        return

    scan_list = scan_lists[0]
    clk = None
    edge = "rising"
    instances = []
    for inst in scan_list["insts"]:
        instance_name = inst
        if isinstance(inst, dict):
            clk = inst.get("clk", clk)
            edge = inst.get("edge", edge)
            instance_name = inst.get("name")
        instances.append(
            {
                "clk": clk,
                "edge": edge,
                "name": instance_name,
            }
        )

    chain_length = len(instances)

    tm_s = config["DFT_TEST_MODE_WIRE"]
    tck_s = config["DFT_TEST_CLOCK_WIRE"]
    sci_s = config["DFT_SCAN_IN_PATTERN"].format(0)
    sco_s = config["DFT_SCAN_OUT_PATTERN"].format(0)
    sce_s = config["DFT_SCAN_ENABLE_PATTERN"].format(0)

    tm = getattr(dut, tm_s)
    tck = getattr(dut, tck_s)
    sci = getattr(dut, sci_s)
    sco = getattr(dut, sco_s)
    sce = getattr(dut, sce_s)

    test_clock = Clock(tck, 10, units="us")

    tm.value = 1

    if excluded := config["DFT_BSCAN_EXCLUDE_IO"]:
        for io in excluded:
            value_to_coerce = 1
            if io.startswith("!"):
                value_to_coerce ^= 1
                io = io[1:]
            port = getattr(dut, io)
            port.value = value_to_coerce

    pattern = random.getrandbits(chain_length)
    scan_in_reg = BinaryValue(pattern, n_bits=chain_length, bigEndian=False)
    scan_out_reg = BinaryValue(0, n_bits=chain_length, bigEndian=False)

    cocotb.start_soon(test_clock.start(start_high=False))

    # dut.rst.value = 0
    for _ in range(0, 4):  # wait a couple cycles for clock multiplexers and such
        await RisingEdge(dut.clk)
        continue
    # dut.rst.value = 1

    await RisingEdge(dut.clk)
    sce.value = 1
    for _ in range(chain_length):
        sci.value = scan_in_reg & 1
        # >>= is a rotation operation
        scan_in_reg = BinaryValue(
            scan_in_reg >> 1, n_bits=chain_length, bigEndian=False
        )
        await RisingEdge(dut.clk)

    await RisingEdge(dut.clk)

    for _ in range(chain_length):
        # >>= is a rotation operation
        scan_out_reg = BinaryValue(
            scan_out_reg >> 1, n_bits=chain_length, bigEndian=False
        )
        scan_out_reg[chain_length - 1] = int(sco.value)
        await RisingEdge(dut.clk)

    print("-", f"{pattern:b}".zfill(chain_length))
    print("+", f"{scan_out_reg.integer:b}".zfill(chain_length))
    print("^", f"{pattern ^ scan_out_reg.integer:b}".zfill(chain_length))

    assert scan_out_reg == pattern, "Chain failed verification"


if __name__ == "__main__":
    # keep click import scoped in case the cocotb environment doesnt
    # have click installed
    import click

    @click.command()
    @click.option(
        "--config",
        required=True,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    )
    # @click.option(
    #     "-D",
    #     "--define",
    #     type=str,
    #     multiple=True,
    # )
    @click.option(
        "--chain-yml",
        required=True,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    )
    @click.argument("sources", nargs=-1)
    def main(config, chain_yml, sources):
        config_dict = json.load(open(config, encoding="utf8"))
        runner = get_runner(config_dict["DFT_COCOTB_SIM"])
        print("%OL_CREATE_REPORT compile.rpt")
        runner.build(
            sources=sources,
            defines={"FUNCTIONAL": True},
            hdl_toplevel=config_dict["DESIGN_NAME"],
            always=True,
            waves=True,
        )
        print("%OL_END_REPORT")
        runner.test(
            hdl_toplevel=config_dict["DESIGN_NAME"],
            test_module="validate_chain,",
            extra_env={"CURRENT_CHAIN_YML": chain_yml, "STEP_CONFIG": config},
            waves=True,
        )

    main()
