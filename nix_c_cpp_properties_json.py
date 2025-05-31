import os
import json
from pathlib import Path
import shlex
import shutil
import sys

top = {
    "configurations": [],
    "version": 4
}
if sys.platform == "darwin":
    clang = shutil.which("clang")
    ys = Path(shutil.which("yosys"))
    yosys_include = str(ys.parent.parent / "share" / "yosys" / "include")
    top["configurations"].append(
        {
            "name": "Nix Config (macOS)",
            "macFrameworkPath": [
                "/System/Library/Frameworks",
                "/Library/Frameworks"
            ],
            "intelliSenseMode": "macos-clang-x64",
            "compilerPath": clang,
            "includePath": ["${workspaceFolder}/yosys-plugin/include", yosys_include],
            "compilerArgs": shlex.split(os.environ["NIX_CFLAGS_COMPILE"])
        }
    )
else:
    print("Script not implemented for your platform yet.", file=sys.stderr)
    exit(-1)

with open(".vscode/c_cpp_properties.json", "w") as f:
    json.dump(top, fp=f)
