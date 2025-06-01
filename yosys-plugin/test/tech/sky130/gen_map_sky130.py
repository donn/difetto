import json
import libparse
from pathlib import Path

in_file = "sky130_fd_sc_hd__tt_025C_1v80.lib"
if False:
    import ciel
    from ciel.source import StaticWebDataSource

    ver = ciel.fetch(
        ciel.get_ciel_home(),
        "sky130",
        "0fe599b2afb6708d281543108caf8310912f54af",
        data_source=StaticWebDataSource(
            "https://fossi-foundation.github.io/ciel-releases"
        ),
    )

    in_file = open(
        Path(ver.get_dir(ciel.get_ciel_home()))
        / "sky130A"
        / "libs.ref"
        / "sky130_fd_sc_hd"
        / "lib"
        / "sky130_fd_sc_hd__tt_025C_1v80.lib"
    )

x = libparse.LibertyParser(in_file)
ast = x.ast
ffs = set()
scannable_cells = {}
for child in ast.children:
    if child.id == "cell":
        name = child.args[0]
        for gc in child.children:
            if gc.id == "ff":
                ffs.add(name)

for ff in ffs:
    pfx, name = ff.split("__")
    scan_equiv = f"{pfx}__s{name}"
    if scan_equiv in ffs:
        scannable_cells[ff] = scan_equiv

final_dict = {"meta": {"version": 1}, "mapping": {}}
for cell, scannable_cell in scannable_cells.items():
    final_dict["mapping"][cell] = scannable_cell


with open("sky130_mapping.json", "w") as f:
    json.dump(final_dict, fp=f)
