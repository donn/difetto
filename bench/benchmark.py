# SPDX-License-Identifier: Unlicense
# Copyright (c) 2025 Mohamed Gaber
import curses
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
from time import sleep
from librelane.flows import Flow, FlowError
from librelane.logging import set_log_level, options
from pathlib import Path
import math
import queue
import fnmatch

__file_dir__ = Path(__file__).absolute().parent
difetto_root = __file_dir__.parent

tests_dir = difetto_root / "yosys-plugin" / "test" / "iscas_89" / "rtl"

status = {}
q = queue.Queue()


def run_test(tup):
    test_path, chain = tup
    global status
    test_name = test_path.stem
    status[tup] = "P"
    design_dir = __file_dir__ / "tests" / test_name
    try:
        design_dir.mkdir(parents=True, exist_ok=True)
        top_clean = design_dir / f"top_{chain}.v"
        with open(design_dir / "ys.log", "w", encoding="utf8") as f:
            subprocess.check_call(
                [
                    "yosys",
                    "-y",
                    tests_dir.parent / "fix_vdd_gnd_inputs.py",
                    "--",
                    test_path,
                    top_clean,
                ],
                stdout=f,
                stderr=subprocess.STDOUT,
            )
        # run
        design_name = test_name
        if test_name.endswith("a") or test_name.endswith("b"):
            design_name = design_name[:-1]
        skips = ["Verilator.Lint"]
        opt_strat = True
        if chain == "basic":
            opt_strat = False
        MyFlow = {
            "skip": Flow.factory.get("DifettoPNRNoChain"),
            "fault": Flow.factory.get("DifettoPNRTopologicalChain"),
            "basic": Flow.factory.get("DifettoPNR"),
            "opt": Flow.factory.get("DifettoPNR"),
        }[chain]
        f = MyFlow(
            {
                "DESIGN_NAME": design_name,
                "VERILOG_FILES": [top_clean],
                "CLOCK_PORT": "CK",
                "CLOCK_PERIOD": 10,
                "FP_CORE_UTIL": 45,
                "DFT_TEST_MODE_WIRE": "tm",
                "DFT_TEST_CLOCK_WIRE": "CK",
                "DFT_SCAN_IN_PATTERN": "sci",
                "DFT_SCAN_OUT_PATTERN": "sco",
                "DFT_SCAN_ENABLE_PATTERN": "sce",
                "DFT_JSON_MAPPING": difetto_root / "test" / "sky130_mapping.json",
                "DFT_BSCAN_EXCLUDE_IO": ["CK", "tm", "!reset", "sce", "sci", "sco"],
                "SYNTH_WRITE_NOATTR": False,
                "DFT_SCAN_OPT": opt_strat,
                # i want the RAW timing
                "DRT_THREADS": 1,
                "RUN_POST_CTS_RESIZER_TIMING": False,
                "RUN_POST_GRT_RESIZER_TIMING": False,
            },
            design_dir=design_dir,
            pdk="sky130A",
        )
        f.start(
            tag=f"benchmark_{chain}",
            overwrite=True,
            skip=skips,
            to="openroad.stapostpnr",
        )
        status[tup] = "S"
    except FlowError as e:
        with open(design_dir / f"out_{chain}.log", "w") as f:
            f.write(str(e))
        status[tup] = "F"
    except Exception as e:
        with open(design_dir / f"out_{chain}.log", "w") as f:
            f.write(str(e))
        status[tup] = "E"


options.set_show_progress_bar(False)
options.set_condensed_mode(True)
set_log_level(40)


pattern = "*"
if len(sys.argv) > 1:
    pattern = sys.argv[1]


def run_tests(screen: curses.window):
    global status

    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
    max_y, max_x = screen.getmaxyx()

    for test in sorted(tests_dir.glob("*.v")):
        if test.stem == "s1488":
            continue
        if not fnmatch.fnmatch(test.stem, pattern):
            continue
        for chain in ["basic", "opt", "skip", "fault"]:
            status[(test, chain)] = "N"

    max_test_width = max(len(str(test.stem)) for test, chain in status)
    test_cell_width = max_test_width + 5  # space opt space indicator space
    tests_per_line = max_x // test_cell_width
    lines_for_tests = math.ceil(len(status) // tests_per_line)
    if max_y < lines_for_tests:
        screen.addstr("window too small")
        screen.refresh()
        screen.getkey()
        exit(-1)

    tpe = ThreadPoolExecutor(16)
    futures = tpe.map(run_test, status)

    while True:
        x = 0
        y = 0
        screen.clear()
        try:
            for test, chain in status:
                value = status[(test, chain)]
                if x + test_cell_width >= max_x:
                    x = 0
                    y += 1
                screen.addstr(y, x, test.stem, curses.color_pair(1))
                screen.addstr(
                    y,
                    x + test_cell_width - 4,
                    {"opt": "3", "basic": "2", "fault": "1", "skip": "0"}[chain],
                )
                screen.addstr(
                    y,
                    x + test_cell_width - 2,
                    value,
                    curses.color_pair({"N": 1, "P": 2, "S": 3, "F": 4, "E": 5}[value]),
                )
                x += test_cell_width
            screen.refresh()
        except curses.error as e:
            screen.addstr(0, 0, str(e) + f"@{x, y}")
            screen.refresh()
        sleep(5)


curses.wrapper(run_tests)
