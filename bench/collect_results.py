# SPDX-License-Identifier: Unlicense
# Copyright (c) 2025 Mohamed Gaber
import csv
import sys
import json
import yaml
from pathlib import Path

__file_dir__ = Path(__file__).parent

rows = []

for test in sorted(__file_dir__.glob("tests/*")):
    test_name = test.stem
    final_dirs = list(test.glob("runs/*/final"))
    if len(final_dirs) < 3:
        print(f"{test_name} not done, skipping…", file=sys.stderr)
        continue
    print(f"Processing {test_name}…", file=sys.stderr)
    row = {"test": test_name}
    for final_dir in sorted(final_dirs):
        strat = final_dir.parent.stem.removeprefix("benchmark_")
        with open(final_dir / "metrics.json") as f:
            metrics = json.load(f)
        drt_dir = next(final_dir.parent.glob("*-openroad-detailedrouting"))
        if strat == "opt":
            dft_dir = next(final_dir.parent.glob("*-difetto-chain"))
            row["core_area"] = metrics["design__core__area"]
            row["chain_length"] = len(
                yaml.safe_load(next(dft_dir.glob("*.chain.yml")).read_text())[0][
                    "partitions"
                ][0]["scan_lists"][0]["insts"]
            )
            row["scannable_element_density"] = row["chain_length"] / row["core_area"]
            row["ys_cell_count"] = metrics["design__instance__count"]
            row["twl_internal_before"] = metrics[
                "dft__chain_twl_internal__init__chain:chain_0"
            ]
            row["twl_internal_after"] = metrics[
                "dft__chain_twl_internal__post_opt__chain:chain_0"
            ]
            row["twl_internal_reduction_pct"] = (
                (float(row["twl_internal_before"]) - float(row["twl_internal_after"]))
                / row["twl_internal_before"]
                * 100
            )
            row["twl_before"] = metrics["dft__chain_twl__init__chain:chain_0"]
            row["twl_after"] = metrics["dft__chain_twl__post_opt__chain:chain_0"]
            row["twl_reduction_pct"] = (
                (float(row["twl_before"]) - float(row["twl_after"]))
                / row["twl_before"]
                * 100
            )
        row[f"setup_ws_{strat}"] = metrics["timing__setup__ws"]
        row[f"hold_ws_{strat}"] = metrics["timing__hold__ws"]
        row[f"routing_time_{strat}"] = open(drt_dir / "runtime.txt").read()
    rows.append(row)

cols = sorted(list(rows[0]))
cols.remove("test")
with open("out.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["test"] + cols)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

print("Done", file=sys.stderr)
