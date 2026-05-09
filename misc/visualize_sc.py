import sys
import yaml
from matplotlib.pyplot import subplots
import matplotlib

from reader import OdbReader

# matplotlib.use("qtagg")


reader = OdbReader(sys.argv[1])
bbox = reader.block.getBBox()


def l1d(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return abs(x2 - x1) + abs(y2 - y1)


if len(sys.argv) > 2:
    with open(sys.argv[2], encoding="utf8") as f:
        chain_data = yaml.safe_load(f)
    insts_raw = chain_data[0]["partitions"][0]["scan_lists"][0]["insts"]
    insts = []
    for inst_raw in insts_raw:
        name = inst_raw
        if not isinstance(name, str):
            name = name["name"]
        inst_found = reader.block.findInst(name)
        assert inst_found is not None, f"no instance {name} found"
        insts.append(inst_found)
else:
    dft = reader.block.getDft()
    chain = dft.getScanChains()[0]
    partition = chain.getScanPartitions()[0]
    scan_list = partition.getScanLists()[0]
    scan_insts = scan_list.getScanInsts()
    insts = list(si.getInst() for si in reversed(scan_insts))

src_placed, src_x, src_y = reader.block.findBTerm("sci").getFirstPinLocation()
sink_placed, sink_x, sink_y = reader.block.findBTerm("sco").getFirstPinLocation()

assert src_placed and sink_placed

fig, ax = subplots()
xs, ys = list(zip(*(inst.getOrigin() for inst in insts)))
ax.plot([src_x, sink_x], [src_y, sink_y], "ro")
ax.plot(xs, ys, "go")
last = (src_x, src_y)
twl = 0
for inst in insts:
    frm = last
    to = inst.getOrigin()
    twl += l1d(frm, to)
    ax.plot((frm[0], to[0]), (frm[1], to[1]), "g")
    last = to
twl += l1d(last, (sink_x, sink_y))
ax.plot((last[0], sink_x), (last[1], sink_y), "g")
print(f"Scannable element count: {len(insts)}")
print(f"Total Wire Length: {twl}")
twl_baseline = twl
fig.savefig("chain.svg")
fig.show()
input()
