import os
import sys
import libyosys as ys


def _Design_run_pass(self, *command):
    ys.Pass.call__YOSYS_NAMESPACE_RTLIL_Design__std_vector_string_(self, list(command))


ys.Design.run_pass = _Design_run_pass  # type: ignore

d = ys.Design()
d.run_pass("read_verilog", "-sv", f"rtl/{sys.argv[1]}")
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
test_port = top.addWire(ys.IdString("\\test"))
test_port.port_input = True
top.fixup_ports()
d.run_pass("write_verilog", "-noattr", f"out/{os.path.basename(sys.argv[1])}/fixed.v")
