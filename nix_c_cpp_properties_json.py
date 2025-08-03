import os
import sys
import json
import shlex
import shutil
import platform
from pathlib import Path

top = {"configurations": [], "version": 4}
arch_string = "x64"
match platform.machine():
    case "arm64":
        arch_string = "arm64"
    case "aarch64":
        arch_string = "arm64"

if platform.system() == "Darwin":
    clang = shutil.which("clang")
    ys = Path(shutil.which("yosys"))
    yosys_include = str(ys.parent.parent / "share" / "yosys" / "include")
    top["configurations"].append(
        {
            "name": "Nix Config (macOS)",
            "macFrameworkPath": ["/System/Library/Frameworks", "/Library/Frameworks"],
            "intelliSenseMode": f"macos-clang-{arch_string}",
            "compilerPath": clang,
            "includePath": ["${workspaceFolder}/yosys-plugin/include", yosys_include],
            "compilerArgs": shlex.split(os.environ["NIX_CFLAGS_COMPILE"]),
        }
    )
else:
    print("Script not implemented for your platform yet.", file=sys.stderr)
    exit(-1)

with open(".vscode/c_cpp_properties.json", "w") as f:
    json.dump(top, fp=f, indent=2)
