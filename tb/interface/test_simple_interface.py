# Copyright 2023 @ cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import os
from secrets import choice, randbits
from typing import Dict, List

import cocotb
import pytest
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.result import TestSuccess
from cocotb.runner import Simulator, get_runner
from cocotb.triggers import ClockCycles, RisingEdge, Timer

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
    DIGEST_WIDTH = int(cocotb.top.DigestWidth)

# Base addresses
CTRL_ADDR = 0x000
BLOCK_ADDR = 0x100
DIGEST_ADDR = 0x200


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

    dut.idle_i.value = 0
    dut.hold_i.value = 0

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


async def block_registers_access(dut, test_id) -> None:
    """

    Write operation is performed with random data and valid address.
    The address is read back and it is expected to find the previously
    written data.

    """

    await init(dut)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) + BLOCK_ADDR
        for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    data: int = randbits(DATA_WIDTH)
    regaddr: int = choice(REGS_ADDR)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    dut._log.info(f"Register access with data = {data:#x} at address = {regaddr:#x}.")

    await master.write(address=regaddr, value=data)
    dut._log.debug(f"Write: {data:#x} at address {regaddr:#x}")

    await ClockCycles(dut.clk_i, 5)

    regval = await master.read(address=regaddr)
    regval = int(regval.value)
    dut._log.debug(f"Read: {regval:#x} at address {regaddr:#x}")

    assert regval == data, (
        f"Test {test_id}:",
        f"Expected {data:#x} at address {regaddr:#x}, " f"read {regval:#x}",
    )


async def invalid_block_registers_access(dut, test_id) -> None:
    """Error response from slave interface

    Write operation is performed with random data and invalid address.
    It is checked whether an error response is sent back.

    """

    await init(dut)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) + BLOCK_ADDR
        for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    maxaddr: int = BLOCK_WIDTH >> 3 if BYTE_ALIGN == 1 else BLOCK_WIDTH >> 5
    INVALID_REGS_ADDR: List[int] = [
        addr for addr in range(maxaddr, maxaddr + BLOCK_ADDR) if addr not in REGS_ADDR
    ]

    if not INVALID_REGS_ADDR:
        raise TestSuccess(
            f"No invalid addresses for BlockWidth = {BLOCK_WIDTH}, ",
            f"DataWidth = {DATA_WIDTH} and ByteAlign = {BYTE_ALIGN}",
        )

    data: int = 0x55
    regaddr: int = choice(INVALID_REGS_ADDR)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    dut._log.info(
        f"Invalid register access with data = {data:#x} at address = {regaddr:#x}."
    )

    await master.write(address=regaddr, value=data)
    dut._log.debug(f"Write: {data:#x} at address {regaddr:#x}")

    # Wait next cycle for response
    await RisingEdge(dut.clk_i)

    error: int = int(dut.rsperror_o.value)

    assert (
        error == 1
    ), f"Test {test_id}: Expected an error response at address {regaddr:#x}."

    await ClockCycles(dut.clk_i, 5)


async def strobe_block_registers_accesses(dut, test_id) -> None:
    """Access the block registers with random strobe value

    Write operations are performed with random data and valid addresses.
    This tests that only valid bytes are written.

    """

    await init(dut)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) + BLOCK_ADDR
        for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    data: int = randbits(DATA_WIDTH)
    validbytes: int = randbits(DATA_WIDTH >> 3)
    regaddr: int = choice(REGS_ADDR)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    # Read register before write operation
    prev_regval = await master.read(address=regaddr)

    expval: int = sim_strobe_write(prev_regval.value, data, validbytes, DATA_WIDTH >> 3)

    dut._log.info(
        f"Register access with data = {data:#x} at address = {regaddr:#x}, with strobe = {validbytes:#x}."
    )

    # Write to the register
    await master.write(address=regaddr, value=data, strobe=validbytes)

    await ClockCycles(dut.clk_i, 5)

    regval = await master.read(address=regaddr)
    regval = int(regval.value)

    dut._log.debug(f"Read: {regval:#x} at address {regaddr:#x}")

    assert regval == expval, (
        f"Test {test_id}:",
        f"Expected {expval:#x} at address {regaddr:#x}, read {regval:#x}",
    )


async def digest_register(dut, test_id) -> None:
    """Digest register access

    Read operations are performed on the digest register.

    """

    await init(dut)

    # Give a random value to the digest input
    digest = randbits(DIGEST_WIDTH)

    REGS_ADDR: List[int] = [
        align(addr, BYTE_ALIGN) + DIGEST_ADDR
        for addr in range(0, DIGEST_WIDTH, DATA_WIDTH)
    ]

    SHL = 3 if BYTE_ALIGN else 5

    regaddr: int = choice(REGS_ADDR)

    nbits = (regaddr & 0xFF) << SHL
    mask = ((1 << DATA_WIDTH) - 1) << nbits
    expval = (digest & mask) >> nbits

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    dut.digest_i.value = digest

    await ClockCycles(dut.clk_i, 5)

    # Read operations on the digest register

    regval = await master.read(address=regaddr)
    regval = int(regval.value)

    dut._log.debug(f"Digest: {digest:#x} with mask {mask:#x}")
    dut._log.info(f"Register read with address = {regaddr:#x}.")

    assert regval == expval

    assert regval == expval, (
        f"Test {test_id}:",
        f"Expected {expval:#x} at address {regaddr:#x}, " f"read {regval:#x}",
    )


# Automatic tests generation depending on requested number of iterations

cocotb_tests = [
    block_registers_access,
    invalid_block_registers_access,
    strobe_block_registers_accesses,
    digest_register,
]

for func_test in cocotb_tests:
    factory = TestFactory(func_test)
    factory.add_option(name="test_id", optionlist=range(ITERATIONS))
    factory.generate_tests()


# This test only needs one iteration


@cocotb.test()
async def control_register(dut) -> None:
    """Control register accesses

    Write and read operations are performed on the control register.

    """

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    await Timer(35, units="ns")

    # Turn off reset
    dut.rst_ni.value = 1

    await ClockCycles(dut.clk_i, 5)

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    # Enable computation

    await master.write(address=CTRL_ADDR, value=0x1)

    await ClockCycles(dut.clk_i, 5)

    regval = await master.read(address=CTRL_ADDR)
    regval = int(regval.value)

    assert regval == 0x1
    assert dut.enable_hash_o.value == 0x1

    dut._log.debug(">> Hash enabled")

    # Reset computation

    await master.write(address=CTRL_ADDR, value=0x2)

    await RisingEdge(dut.clk_i)

    assert dut.reset_hash_o.value == 0x1

    regval = await master.read(address=CTRL_ADDR)
    assert regval == 0x0
    assert dut.enable_hash_o.value == 0x0

    dut._log.debug(">> Hash reset")

    # Deassert enable with idle or hold

    await master.write(address=CTRL_ADDR, value=0x1)

    await ClockCycles(dut.clk_i, 5)

    dut.idle_i.value = 0x1

    await ClockCycles(dut.clk_i, 2)

    assert dut.enable_hash_o.value == 0x0

    dut._log.debug(">> Hash deasserted by idle signal")


@pytest.mark.parametrize("DataWidth", ["8", "16", "32", "64", "128"])
@pytest.mark.parametrize("BlockWidth", ["512", "1024"])
@pytest.mark.parametrize("ByteAlign", ["1'b0", "1'b1"])
@pytest.mark.parametrize("DigestWidth", ["224", "256"])
def test_sha_regs(DataWidth, BlockWidth, ByteAlign, DigestWidth):
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

    dut: str = "simple_reg_interface"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = "simple_reg_interface"

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
    parameters["DigestWidth"] = DigestWidth

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
