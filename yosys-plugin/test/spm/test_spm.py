import os
import re
import pytest
from pathlib import Path
import subprocess

cwd = Path(__file__).resolve().parent


def run(title, *args):
    env = os.environ.copy()
    env["DIFETTO_SO"] = pytest.difetto
    env["TECH_DIR"] = pytest.test_root / "tech"
    args_resolved = [str(e) for e in args]
    p = subprocess.check_output(args_resolved, cwd=cwd, env=env, encoding="utf8")
    with open(cwd / "out" / f"{title}.log", "w", encoding="utf8") as f:
        f.write(p)
    return p


def test_spm():
    run("synth", "yosys", "-c", cwd / "synth.tcl")
    run("cut", "yosys", "-c", cwd / "cut.tcl")
    run(
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
        "atpg",
        "quaigh",
        "atpg",
        "-o",
        cwd / "out" / "spm.raw_tvs.txt",
        cwd / "out" / "spm.bench",
    )
    coverage_rx = re.compile(r"([\d.]+)% coverage")
    atpg_result = coverage_rx.search(atpg_result)
    assert atpg_result is not None, "No coverage found"
    coverage = float(atpg_result[1])
    assert coverage > 95, "Coverage too low"
