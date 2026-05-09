import os
import sys
import json
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.handle import HierarchyObject
from cocotb_tools.runner import get_runner

from scan_chain import run_scan

__file_dir__ = Path(__file__).absolute().parent

sys.path.append(str(__file_dir__.parent / "common"))

from patterns import read_patterns_bin


@cocotb.test()
async def chain_test(dut: HierarchyObject):
    """Test that the chain is valid"""

    batch_from = int(os.environ["BATCH_FROM"])
    batch_to = int(os.environ["BATCH_TO"])

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

    test_clock = Clock(tck, 10, unit="us")

    if excluded := config["DFT_BSCAN_EXCLUDE_IO"]:
        for io in excluded:
            value_to_coerce = 0
            if io.startswith("!"):
                value_to_coerce ^= 1
                io = io[1:]
            port = getattr(dut, io)
            port.value = value_to_coerce
    cocotb.start_soon(test_clock.start(start_high=False))

    step_dir = Path(os.environ["STEP_DIR"])
    diff_dir = step_dir / "diffs"
    diff_dir.mkdir(parents=True, exist_ok=True)

    bad_values = 0
    with (
        open(os.environ["CURRENT_TVS"], "rb") as tvs_f,
        open(os.environ["CURRENT_AU"], "rb") as au_f,
    ):
        for i, (tv, au) in enumerate(
            zip(read_patterns_bin(tvs_f), read_patterns_bin(au_f))
        ):
            if i < batch_from or (batch_to != -1 and i > batch_to):
                continue
            cocotb.log.info(f"Running test vector {i}…")
            with open(diff_dir / f"tv_{i}.log", "w", encoding="utf8") as diff_f:
                diff = await run_scan(
                    tck,
                    tm,
                    sce,
                    sci,
                    sco,
                    tv,
                    au,
                    mask,
                    diff_file=diff_f,
                    wait_cycle=True,
                )

            if diff.count(1) != 0:
                bad_values += 1
                cocotb.log.error(f"Test vector {i} failed.")
            else:
                cocotb.log.info(f"Test vector {i} succeeded.")

    assert bad_values == 0, "One or more test chains did not respond as expected."


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
    @click.option(
        "--batch-from",
        required=False,
        type=int,
        default=0,
    )
    @click.option(
        "--batch-to",
        required=False,
        type=int,
        default=-1,
    )
    @click.argument("sources", nargs=-1)
    def main(step_dir, config, au, tvs, mask, sources, batch_from, batch_to):
        config_dict = json.load(open(config, encoding="utf8"))
        runner = get_runner(config_dict["DFT_COCOTB_SIM"])
        print("%OL_CREATE_REPORT compile.rpt", flush=True)
        extra_build_kwargs = {}
        if timescale_tuple := config_dict["DFT_COCOTB_TIMESCALE"]:
            extra_build_kwargs["timescale"] = tuple(timescale_tuple)
        runner.build(
            sources=sources,
            defines={"FUNCTIONAL": True},
            hdl_toplevel=config_dict["DESIGN_NAME"],
            always=True,
            waves=True,
            build_dir=os.getenv("SIM_BUILD", "sim_build"),
            **extra_build_kwargs,
        )
        print("%OL_END_REPORT", flush=True)
        extra_env = {
            "CURRENT_AU": au,
            "CURRENT_TVS": tvs,
            "CURRENT_MASK": mask,
            "STEP_CONFIG": config,
            "STEP_DIR": step_dir,
            "BATCH_FROM": str(batch_from),
            "BATCH_TO": str(batch_to),
        }
        runner.test(
            hdl_toplevel=config_dict["DESIGN_NAME"],
            test_module="run_tvs,",
            extra_env=extra_env,
            waves=True,
        )

    main()
