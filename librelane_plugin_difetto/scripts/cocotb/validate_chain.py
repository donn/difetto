import os
import sys
import json
import random
from pathlib import Path

import yaml
from bitarray import bitarray

import cocotb
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject
from cocotb.runner import get_runner

from scan_chain import run_scan

__file_dir__ = Path(__file__).absolute().parent

sys.path.append(str(__file_dir__.parent / "common"))

from chain import load_chains


@cocotb.test()
async def chain_test(dut: HierarchyObject):
    """Test that the chain is valid"""

    config_json = os.environ["STEP_CONFIG"]
    chain_yml = os.environ["CURRENT_CHAIN_YML"]

    with open(config_json, encoding="utf8") as f:
        config = json.load(f)

    with open(chain_yml, encoding="utf8") as f:
        chain_list_raw = yaml.load(f, Loader=yaml.SafeLoader)

    chains = load_chains(chain_list_raw)
    if len(chains) == 0:
        cocotb.log.warning("No chains found.")
        return
    assert len(chains) == 1, "multiple chains not supported"
    chain = chains[0]
    chain_length = chain.get_length_of_uniform_chain()
    if chain_length == 0:
        cocotb.log.warning("Chain is empty.")
        return

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

    if excluded := config["DFT_BSCAN_EXCLUDE_IO"]:
        for io in excluded:
            value_to_coerce = 1
            if io.startswith("!"):
                value_to_coerce ^= 1
                io = io[1:]
            port = getattr(dut, io)
            port.value = value_to_coerce

    pattern = bitarray(f"{random.getrandbits(chain_length):b}".zfill(chain_length))

    cocotb.start_soon(test_clock.start(start_high=False))

    diff = await run_scan(
        tck,
        tm,
        sce,
        sci,
        sco,
        pattern,
        pattern,
        bitarray("1" * chain_length),
        wait_cycle=False,
    )
    assert diff.count(1) == 0, "Chain failed verification"


if __name__ == "__main__":
    # keep click import scoped in case the cocotb environment doesnt
    # have click installed
    import click

    @click.command()
    @click.option(
        "--step-dir",
        required=True,
        type=click.Path(
            exists=False,
            file_okay=False,
            dir_okay=True,
        ),
    )
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
    def main(step_dir, config, chain_yml, sources):
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
            extra_env={
                "CURRENT_CHAIN_YML": chain_yml,
                "STEP_CONFIG": config,
                "STEP_DIR": step_dir,
            },
            waves=True,
        )

    main()
