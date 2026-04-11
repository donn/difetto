# SPDX-License-Identifier: Unlicense
# Copyright (c) 2025 Mohamed Gaber
from pathlib import Path
from datetime import timedelta, datetime
import sys

run = Path(sys.argv[1])
total = timedelta()
zero_time = datetime.strptime("00:00:00.000", "%H:%M:%S.%f")
print("step_dir,time")
for step in sorted(run.glob("*/runtime.txt")):
    step_time = open(step).read()
    print(f"{step.parent.stem},{step_time}")
    total += datetime.strptime(step_time, "%H:%M:%S.%f") - zero_time
print(f"sum,{total}")
