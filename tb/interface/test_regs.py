import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
from cocotb.result import TestSuccess
from cocotb.runner import get_runner, Simulator

import os
import pytest
from secrets import choice, randbits
from typing import Dict, List

from bus.master import Master

ITERATIONS = int(os.getenv("ITERATIONS", 10))
SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")

if cocotb.simulator.is_running():
    DATA_WIDTH = int(cocotb.top.DataWidth)
    ADDR_WIDTH = int(cocotb.top.AddrWidth)
    BLOCK_WIDTH = int(cocotb.top.BlockWidth)
    BYTE_ALIGN = int(cocotb.top.ByteAlign)


MAPPING: Dict[str, str] = {
    "reqdata": "reqdata_i",
    "reqaddr": "reqaddr_i",
    "reqvalid": "reqvalid_i",
    "reqwrite": "reqwrite_i",
    "reqready": "reqready_o",
    "reqstrobe": "reqstrobe_i",
    "rspready": "rspready_i",
    "rspvalid": "rspvalid_o",
    "rspdata": "rspdata_o",
    "rsperror": "rsperror_o",
}


@cocotb.coroutine
async def init(dut):
    """Initialize input signals value"""

    """ 

    This would be the correct way to do it.
    But verilator does not support it so the list must be maintained by hand.

    for signal in dir(sha):
        if signal.endswith('_i') and signal != "clk_i":
            dut._id(signal, extended=False).value = 0 
            
    """

    dut.reqdata_i.value = 0
    dut.reqaddr_i.value = 0
    dut.reqvalid_i.value = 0
    dut.reqwrite_i.value = 0
    dut.reqstrobe_i.value = 0
    dut.rspready_i.value = 0

    dut.rst_ni.value = 0

    await Timer(1, units="ns")


def align(addr: int, bytealign: bool):
    step = 8 if bytealign else 32
    return int(addr / step)


def sim_strobe_write(prevval: int, wrval: int, strobe: int, databytes: int) -> int:
    regval: int = 0
    data: int = 0

    for b in range(0, databytes):
        data = wrval if strobe & (1 << b) else prevval
        regval |= data & (0xFF << b * 8)

    return regval


@cocotb.test()
async def registers_accesses(dut) -> None:
    """Access the sha registers

    Write operations are performed with random data and valid addresses.
    The addresses are read back and it is expected to find the previously
    written data.

    """

    await init(dut)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    dut._log.info(f"Random register accesses with {ITERATIONS} iterations.")

    for idx in range(ITERATIONS):
        rndval: int = randbits(DATA_WIDTH)

        # Write to a random register
        regaddr: int = choice(REGS_ADDR)
        await master.write(address=regaddr, value=rndval)
        dut._log.debug(f"Write: {rndval:#x} at address {regaddr:#x}")

        await ClockCycles(dut.clk_i, 5)

        regval = await master.read(address=regaddr)
        regval = int(regval.value)
        dut._log.debug(f"Read: {regval:#x} at address {regaddr:#x}")

        assert regval == rndval, (
            f"Index {idx}: "
            f"Expected {rndval:#x} at address {regaddr:#x}, "
            f"read {regval:#x}"
        )


@cocotb.test()
async def invalid_registers_accesses(dut) -> None:
    """Error response from slave interface

    Write operations are performed with random data and invalid addresses.
    It is checked whether an error response is sent back.

    """

    await init(dut)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    maxaddr: int = BLOCK_WIDTH >> 3 if BYTE_ALIGN == 1 else BLOCK_WIDTH >> 5
    INVALID_REGS_ADDR: List[int] = [
        addr for addr in range(maxaddr) if addr not in REGS_ADDR
    ]

    if not INVALID_REGS_ADDR:
        raise TestSuccess(
            f"No invalid addresses for BlockWidth = {BLOCK_WIDTH}, ",
            f"DataWidth = {DATA_WIDTH} and ByteAlign = {BYTE_ALIGN}",
        )

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    dut._log.info(f"Random invalid register accesses with {ITERATIONS} iterations.")

    wr_val: int = 0x55

    for idx in range(ITERATIONS):
        # Write to an invalid register
        regaddr: int = choice(INVALID_REGS_ADDR)
        await master.write(address=regaddr, value=wr_val)
        dut._log.debug(f"Write: {wr_val:#x} at address {regaddr:#x}")

        error: int = int(dut.rsperror_o.value)

        assert error == 1, (
            f"Index {idx}: " f"Expected an error response at address {regaddr:#x}."
        )

        await ClockCycles(dut.clk_i, 5)


@cocotb.test()
async def strobe_registers_accesses(dut) -> None:
    """Access the sha registers with random strobe value

    Write operations are performed with random data and valid addresses.
    This tests that only valid bytes are written.

    """

    await init(dut)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    dut._log.info(f"Random strobe register accesses with {ITERATIONS} iterations.")

    for idx in range(ITERATIONS):
        rndval: int = randbits(DATA_WIDTH)
        validbytes: int = randbits(DATA_WIDTH >> 3)
        regaddr: int = choice(REGS_ADDR)

        # Read register before write operation
        prev_regval = await master.read(address=regaddr)

        expval: int = sim_strobe_write(
            prev_regval.value, rndval, validbytes, DATA_WIDTH >> 3
        )

        # Write to the register
        await master.write(address=regaddr, value=rndval, strobe=validbytes)
        dut._log.debug(
            f"Write: {rndval:#x} at address {regaddr:#x} with strobe {validbytes:#b}"
        )

        await ClockCycles(dut.clk_i, 5)

        regval = await master.read(address=regaddr)
        regval = int(regval.value)
        dut._log.debug(f"Read: {regval:#x} at address {regaddr:#x}")

        assert regval == expval, (
            f"Index {idx}: "
            f"Expected {expval:#x} at address {regaddr:#x}, "
            f"read {regval:#x}"
        )


@pytest.mark.parametrize("DataWidth", ["8", "16", "32", "64", "128"])
@pytest.mark.parametrize("BlockWidth", ["256", "384", "512"])
@pytest.mark.parametrize("ByteAlign", ["1'b0", "1'b1"])
def test_sha_regs(DataWidth, BlockWidth, ByteAlign):
    """Run cocotb tests on sha1 registers for different combinations of parameters.

    Args:
            DataWidth:  Data bus width.
            BlockWidth: Width of the block to compute
            ByteAlign:  Whether we want an alignment on bytes or words.

    """

    # skip test if there is an invalid combination of parameters
    if ByteAlign == "1'b0" and DataWidth in ["8", "16"]:
        pytest.skip(
            f"Invalid combination: ByteAlign = {ByteAlign} and DataWidth = {DataWidth}"
        )

    tests_dir: str = os.path.dirname(__file__)
    rtl_dir: str = os.path.abspath(
        os.path.join(tests_dir, "..", "..", "hw", "interface")
    )

    dut: str = "reg_interface"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = "reg_interface"

    verilog_sources: List[str] = [
        os.path.join(rtl_dir, f"{dut}.sv"),
    ]

    extra_args: List[str] = []

    if SIM == "verilator" and WAVES == "1":
        extra_args = ["--trace", "--trace-structs"]

    parameters: Dict[str, str] = {}

    parameters["DataWidth"] = DataWidth
    parameters["BlockWidth"] = BlockWidth
    parameters["ByteAlign"] = ByteAlign

    sim_build: str = os.path.join(tests_dir, f"{SIM_BUILD}", f"{dut}_sim_build")

    runner: Simulator = get_runner(simulator_name=SIM)

    runner.build(
        verilog_sources=verilog_sources,
        hdl_toplevel=toplevel,
        always=True,
        build_dir=sim_build,
        build_args=extra_args,
        parameters=parameters,
    )

    runner.test(hdl_toplevel=toplevel, test_module=module)
