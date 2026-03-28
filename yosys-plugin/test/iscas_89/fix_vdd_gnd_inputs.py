import os
import sys
from pyosys import libyosys as ys


def _Design_run_pass(self, *command):
    ys.Pass.call(self, list(command))


ys.Design.run_pass = _Design_run_pass  # type: ignore

d = ys.Design()
d.run_pass("read_verilog", "-sv", sys.argv[1])
d.run_pass("hierarchy", "-auto-top")
d.run_pass("proc")
top = d.top_module()
ports = set([p.str() for p in top.ports])
if "\\VDD" in ports:
    vdd = top.wires_[ys.IdString("\\VDD")]
    vdd.port_input = False
    hi_const = ys.Const(ys.State.S1, 1)
    top.connect(ys.SigSpec(vdd), ys.SigSpec(hi_const))
if "\\GND" in ports:
    gnd = top.wires_[ys.IdString("\\GND")]
    gnd.port_input = False
    lo_const = ys.Const(ys.State.S0, 1)
    top.connect(ys.SigSpec(gnd), ys.SigSpec(lo_const))
if "\\CK" not in ports:
    # combinational design, add clock port for consistency
    clock_port = top.addWire(ys.IdString("\\CK"))
    clock_port.port_input = True
if "\\reset" not in ports:
    # add reset
    reset_port = top.addWire(ys.IdString("\\reset"))
    reset_port.port_input = True
for dft_port in ["\\tm", "\\sci", "\\sce", "\\sco"]:
    wire = top.addWire(dft_port)
    if dft_port == "\\sco":
        wire.port_output = True
    else:
        wire.port_input = True
top.fixup_ports()
d.run_pass("write_verilog", "-noattr", sys.argv[2])
