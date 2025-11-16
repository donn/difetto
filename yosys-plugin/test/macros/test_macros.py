import re
import pytest

from pathlib import Path
import subprocess

cwd = Path(__file__).resolve().parent


def run(test, title, *args):
    args_resolved = [str(e) for e in args]
    out_log_path = cwd / "out" / test / f"{title}.log"
    results_dir = Path(cwd / "out" / test)
    results_dir.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(
        args_resolved,
        cwd=results_dir,
        stdout=open(out_log_path, "w"),
        stderr=subprocess.STDOUT,
        encoding="utf8",
    )
    return out_log_path

def test_macros():
    run("macros", "synth", "yosys", "-gy", cwd / "synth.py")
    run("macros", "cut", "yosys", "-gy", cwd / "cut.py")
    run("macros", "bench", "nl2bench", "-l",
        pytest.test_root / "tech" / "sky130" / "sky130_fd_sc_hd__tt_025C_1v80.lib",
        "--msb-first",
        "-o",
        cwd / "out" / "macros" / "top.bench",
        cwd / "out" / "macros" /  "top.cut.v",
    )
    atpg_result = run(
        "macros",
        "atpg",
        "quaigh",
        "atpg",
        "-o",
        cwd / "out" / "macros" /  "top.raw_tvs.txt",
        cwd / "out" / "macros" /  "top.bench",
    )
    atpg_result_str = open(atpg_result).read()
    coverage_rx = re.compile(r"([\d.]+)% coverage")
    atpg_result = coverage_rx.search(atpg_result_str)
    assert atpg_result is not None, "No coverage found"
    coverage = float(atpg_result[1])
    assert coverage >= 99, "Coverage lower than 99%"
