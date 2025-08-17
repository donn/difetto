import os
import sys
import json

import cocotb
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject
from cocotb.runner import get_runner

from scan_chain import run_scan

__file_dir__ = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(os.path.dirname(__file_dir__), "common"))

from patterns import read_patterns_bin


@cocotb.test()
async def chain_test(dut: HierarchyObject):
    """Test that the chain is valid"""

    config_json = os.environ["STEP_CONFIG"]

    with open(config_json, encoding="utf8") as f:
        config = json.load(f)

    with open(os.environ["CURRENT_MASK"], "rb") as f:
        mask = next(read_patterns_bin(f))

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
    cocotb.start_soon(test_clock.start(start_high=False))

    with open(os.environ["CURRENT_TVS"], "rb") as tvs_f, open(
        os.environ["CURRENT_AU"], "rb"
    ) as au_f:
        for i, (tv, au) in enumerate(
            zip(read_patterns_bin(tvs_f), read_patterns_bin(au_f))
        ):
            diff = await run_scan(tck, tm, sce, sci, sco, tv, au, mask, wait_cycle=True)

            if diff.count(1) != 0:
                cocotb.log.error(f"Test vector {i} failed.")


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
        "--au",
        required=True,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    )
    @click.option(
        "--tvs",
        required=True,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    )
    @click.option(
        "--mask",
        required=True,
        type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    )
    @click.argument("sources", nargs=-1)
    def main(config, au, tvs, mask, sources):
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
            test_module="run_tvs,",
            extra_env={
                "CURRENT_AU": au,
                "CURRENT_TVS": tvs,
                "CURRENT_MASK": mask,
                "STEP_CONFIG": config,
            },
            waves=True,
        )

    main()
