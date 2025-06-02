import os
import re
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


def test_spm():
    run("spm", "synth", "yosys", "-c", cwd / "synth.tcl")
    run("spm", "cut", "yosys", "-c", cwd / "cut.tcl")
    run(
        "spm",
        "bench",
        "nl2bench",
        "-l",
        pytest.test_root / "tech" / "sky130" / "sky130_fd_sc_hd__tt_025C_1v80.lib",
        "--msb-first",
        "-o",
        cwd / "out" / "spm.bench",
        cwd / "out" / "spm.cut.v",
    )
    atpg_result = run(
        "spm",
        "atpg",
        "quaigh",
        "atpg",
        "-o",
        cwd / "out" / "spm.raw_tvs.txt",
        cwd / "out" / "spm.bench",
    )
    atpg_result_str = open(atpg_result).read()
    coverage_rx = re.compile(r"([\d.]+)% coverage")
    atpg_result = coverage_rx.search(atpg_result_str)
    assert atpg_result is not None, "No coverage found"
    coverage = float(atpg_result[1])
    assert coverage == 100, "SPM coverage not 100%"
