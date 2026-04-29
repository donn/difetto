import sys
import json
import csv
from pathlib import Path
from congestion import get_congestion_scores

fieldnames = ["design"]
for score in ["mean", "ratio", "square mean"]:
    for strat in ["skip", "fault", "basic", "opt"]:
        fieldnames.append(f"{score} ({strat})")

out = csv.DictWriter(open("congestion_scores.csv", "w"), fieldnames=fieldnames)
out.writeheader()

for design_dir_raw in sys.argv[1:]:
    design_dir = Path(design_dir_raw)
    if not design_dir.is_dir():
        print(f"{design_dir} is not a valid directory", file=sys.stderr)
        exit(1)
    test_name = design_dir.stem
    final_dirs = list(design_dir.glob("runs/*/final"))
    if len(final_dirs) < 4:
        print(f"{test_name} may not be done.", file=sys.stderr)
        continue
    print(f"Processing {test_name}…", file=sys.stderr)
    row = {}
    for final_dir in sorted(final_dirs):
        row["design"] = design_dir.stem
        strat = final_dir.parent.stem.removeprefix("benchmark_")  # older benchmarks
        if strat == "synth":
            # reusable synth dir, ignore
            continue
        try:
            heatmap_dir = next(
                final_dir.parent.glob("*-openroad-dumpcongestionheatmap")
            )
        except StopIteration:
            heatmap_dir = next(
                final_dir.parent.glob("*-openroad-dumpheatmaps")
            )  # old step
        mean, ratio, square_mean = get_congestion_scores(
            heatmap_dir / "congestion.csv"
        )
        row[f"mean ({strat})"] = mean
        row[f"ratio ({strat})"] = ratio
        row[f"square mean ({strat})"] = square_mean
    out.writerow(row)
