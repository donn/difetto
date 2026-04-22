# SPDX-License-Identifier: Unlicense
# Copyright (c) 2025 Mohamed Gaber
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import re
import sys
import json
import yaml
from pathlib import Path

__file_dir__ = Path(__file__).parent

workbook = xlsxwriter.Workbook("results.xlsx")
worksheet = workbook.add_worksheet()

cols = [
    "Design",
    "Cell Count",
    "Scannable Elements",
    "Scannable Element Ratio",
    "Internal TWL (Pre-Opt)",
    "Internal TWL (Post-Opt)",
    "TWL (Pre-Opt)",
    "TWL (Post-Opt)",
    "TWL Drop",
]
for metric in ["Worst Slack", "Total Negative Slack", "Routing Time"]:
    for strat in ["skip", "fault", "basic", "opt"]:
        cols.append(f"{metric} ({strat})")
    for strat in ["skip", "fault", "basic", "opt"]:
        if strat != "skip":
            cols.append(f"{metric} Impact ({strat})")
cols.append("Routing Threads")

col_by_name = {el: i for i, el in enumerate(cols)}

for el, i in col_by_name.items():
    worksheet.write(0, i, el)

row = 0


def get_elapsed_drt_time(path):
    rx = re.compile(r"elapsed time = ([\d:]+)")
    last = None
    for line in open(path):
        res = rx.search(line)
        if res is None:
            continue
        last = res[1]
    return last

def w(name, data):
    global row
    global worksheet
    global col_by_name
    worksheet.write(row, col_by_name[name], data)

def wf(name, data):
    global row
    global worksheet
    global col_by_name
    worksheet.write_formula(row, col_by_name[name], data)

for design_dir_raw in sys.argv[1:]:
    design_dir = Path(design_dir_raw)
    test_name = design_dir.stem
    final_dirs = list(design_dir.glob("runs/*/final"))
    if final_dirs == 0:
        continue
    if len(final_dirs) < 4:
        print(f"{test_name} may not be done.", file=sys.stderr)
    print(f"Processing {test_name}…", file=sys.stderr)
    row += 1
    for final_dir in sorted(final_dirs):
        strat = final_dir.parent.stem.removeprefix("benchmark_")  # older benchmarks
        if strat == "synth":
            # reusable synth dir, ignore
            continue
        drt_dir = next(final_dir.parent.glob("*-openroad-detailedrouting"))
        with open(drt_dir / "state_out.json") as f:
            state_out = json.load(f)
        metrics = state_out["metrics"]
        with open(drt_dir / "config.json") as f:
            drt_conf = json.load(f)
        w("Design", test_name)
        if strat == "opt":
            dft_dir = next(final_dir.parent.glob("*-difetto-chain"))
            w("Cell Count", metrics["design__instance__count"])
            w(
                "Scannable Elements",
                len(
                    yaml.safe_load(next(dft_dir.glob("*.chain.yml")).read_text())[0][
                        "partitions"
                    ][0]["scan_lists"][0]["insts"]
                ),
            )
            cells_ref = xl_rowcol_to_cell(row, col_by_name["Cell Count"])
            scannable_ref = xl_rowcol_to_cell(row, col_by_name["Scannable Elements"])
            wf(
                "Scannable Element Ratio",
                f"={scannable_ref}/{cells_ref}"
            )
            w("Routing Threads", drt_conf["DRT_THREADS"])
            w(
                "Internal TWL (Pre-Opt)",
                metrics["dft__chain_twl_internal__init__chain:chain_0"],
            )
            w(
                "Internal TWL (Post-Opt)",
                metrics["dft__chain_twl_internal__post_opt__chain:chain_0"],
            )
            w(
                "TWL (Pre-Opt)",
                metrics["dft__chain_twl__init__chain:chain_0"],
            )
            w(
                "TWL (Post-Opt)",
                metrics["dft__chain_twl__post_opt__chain:chain_0"],
            )
            twl_pre_ref = xl_rowcol_to_cell(row, col_by_name["TWL (Pre-Opt)"])
            twl_post_ref = xl_rowcol_to_cell(row, col_by_name["TWL (Post-Opt)"])
        w(f"Worst Slack ({strat})", metrics["timing__setup__ws"])
        w(f"Total Negative Slack ({strat})", metrics["timing__setup__tns"])
        w(f"Routing Time ({strat})", get_elapsed_drt_time(drt_dir / "openroad-detailedrouting.log"))

first_se_ratio = xl_rowcol_to_cell(1, col_by_name["Scannable Element Ratio"])
last_se_ratio = xl_rowcol_to_cell(row, col_by_name["Scannable Element Ratio"])
for metric in ["Worst Slack", "Total Negative Slack", "Routing Time"]:
    for strat in ["fault", "basic", "opt"]:
        base = f"{metric} (skip)"
        ref = f"{metric} ({strat})"
        calculated = f"{metric} Impact ({strat})"
        first = xl_rowcol_to_cell(1, col_by_name[calculated])
        for i in range(1, row+1):
            base_cell = xl_rowcol_to_cell(i, col_by_name[base])
            strat_cell = xl_rowcol_to_cell(i, col_by_name[ref])
            impact_cell = xl_rowcol_to_cell(i, col_by_name[calculated])
            worksheet.write_formula(impact_cell, f"=IF({base_cell}=0, \"\", ({strat_cell}-{base_cell})/{base_cell})")
        last =xl_rowcol_to_cell(row, col_by_name[calculated])
        avg_cell = xl_rowcol_to_cell(row+1, col_by_name[calculated])
        worksheet.write_formula(avg_cell, f"=AVERAGE({first}:{last})")
        median_cell = xl_rowcol_to_cell(row+2, col_by_name[calculated])
        worksheet.write_formula(median_cell, f"=MEDIAN({first}:{last})")
        stdev_cell = xl_rowcol_to_cell(row+3, col_by_name[calculated])
        worksheet.write_formula(stdev_cell, f"=STDEV({first}:{last})")
        correlate_cell = xl_rowcol_to_cell(row+4, col_by_name[calculated])
        worksheet.write_formula(correlate_cell, f"=CORREL({first}:{last},{first_se_ratio}:{last_se_ratio})")

workbook.close()

print("Done", file=sys.stderr)
