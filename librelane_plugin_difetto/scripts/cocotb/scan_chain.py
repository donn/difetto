from bitarray import bitarray

from cocotb.triggers import RisingEdge
from cocotb.binary import BinaryValue


async def run_scan(
    tck,
    tm,
    sce,
    sci,
    sco,
    tv: bitarray,
    au: bitarray,
    mask: bitarray,
    wait_cycle=True,
):
    tm.value = 1
    chain_length = len(tv)
    scan_in_reg = BinaryValue(tv.to01(), n_bits=chain_length, bigEndian=False)
    scan_out_reg = BinaryValue(0, n_bits=chain_length, bigEndian=False)

    # dut.rst.value = 0
    for _ in range(0, 4):  # wait a couple cycles for clock multiplexers and such
        await RisingEdge(tck)
        continue
    # dut.rst.value = 1

    await RisingEdge(tck)
    sce.value = 1
    for _ in range(chain_length):
        sci.value = scan_in_reg & 1
        # >>= is a rotation operation
        scan_in_reg = BinaryValue(
            scan_in_reg >> 1, n_bits=chain_length, bigEndian=False
        )
        await RisingEdge(tck)

    if wait_cycle:
        sce.value = 0
        await RisingEdge(tck)
        sce.value = 1

    for _ in range(chain_length):
        await RisingEdge(tck)
        # >>= is a rotation operation
        scan_out_reg = BinaryValue(
            scan_out_reg >> 1, n_bits=chain_length, bigEndian=False
        )
        scan_out_reg[chain_length - 1] = int(sco.value)

    out = bitarray(scan_out_reg.binstr) & mask
    diff = au ^ out
    print("&", mask.to01())
    print("-", au.to01())
    print("+", out.to01())
    print("^", (au ^ out).to01())

    return diff
