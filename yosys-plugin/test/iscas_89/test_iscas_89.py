import os
import re
import shutil
import pytest
from pathlib import Path
import subprocess

cwd = Path(__file__).resolve().parent


def run(test, title, *args):
    env = os.environ.copy()
    env["DIFETTO_SO"] = pytest.difetto
    env["TECH_DIR"] = pytest.test_root / "tech"
    env["TEST"] = test
    args_resolved = [str(e) for e in args]
    out_log_path = cwd / "out" / test / f"{title}.log"
    Path(cwd / "out" / test).mkdir(parents=True, exist_ok=True)
    p = subprocess.check_call(
        args_resolved,
        cwd=cwd,
        env=env,
        stdout=open(out_log_path, "w"),
        stderr=subprocess.STDOUT,
        encoding="utf8",
    )
    return out_log_path


@pytest.mark.parametrize("test", pytest.iscas_89_tests)
def test_iscas_89_design(test):
    run(test, "fixup", "yosys", "-y", "fix_vdd_gnd_inputs.py", "--", test)
    run(test, "synth", "yosys", "-c", cwd / "synth.tcl")
    run(test, "cut", "yosys", "-c", cwd / "cut.tcl")
    run(
        test,
        "bench",
        "nl2bench",
        "-l",
        pytest.test_root / "tech" / "sky130" / "sky130_fd_sc_hd__tt_025C_1v80.lib",
        "--msb-first",
        "-o",
        cwd / "out" / test / "design.bench",
        cwd / "out" / test / "cut.v",
    )
    atpg_result = run(
        test,
        "atpg",
        "quaigh",
        "atpg",
        "-o",
        cwd / "out" / test / "raw_tvs.txt",
        cwd / "out" / test / "design.bench",
    )
    atpg_result_str = open(atpg_result).read()
    coverage_rx = re.compile(r"([\d.]+)% coverage")
    atpg_result = coverage_rx.search(atpg_result_str)
    assert atpg_result is not None, "No coverage found"
    coverage = float(atpg_result[1])
