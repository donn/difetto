import io
import sys
from bitarray import bitarray

from cocotb.triggers import RisingEdge
from cocotb.types import LogicArray


async def run_scan(
    tck,
    tm,
    sce,
    sci,
    sco,
    tv: bitarray,
    au: bitarray,
    mask: bitarray,
    diff_file: io.TextIOWrapper = sys.stdout,
    wait_cycle=True,
):
    tm.value = 1
    chain_length = len(tv)
    scan_in_reg = LogicArray(tv.to01(), chain_length)
    scan_out_reg = LogicArray(0, chain_length)

    # dut.rst.value = 0
    for _ in range(0, 4):  # wait a couple cycles for clock multiplexers and such
        await RisingEdge(tck)
        continue
    # dut.rst.value = 1

    await RisingEdge(tck)
    sce.value = 1
    for i in range(chain_length):
        sci.value = scan_in_reg[i]
        await RisingEdge(tck)

    if wait_cycle:
        sce.value = 0
        await RisingEdge(tck)
        sce.value = 1

    for i in range(chain_length):
        await RisingEdge(tck)
        scan_out_reg[i] = int(sco.value)

    out = bitarray(scan_out_reg.binstr) & mask
    diff = au ^ out
    if diff_file is not None:
        print("&", mask.to01(), file=diff_file)
        print("-", au.to01(), file=diff_file)
        print("+", out.to01(), file=diff_file)
        print("^", diff.to01(), file=diff_file)

    return diff
