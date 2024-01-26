# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import os
from secrets import randbits
from typing import Dict, List

import cocotb
import pytest
import vsc
from bus.master import Master
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.runner import Simulator, get_runner
from cocotb.triggers import ClockCycles, RisingEdge, Timer
from utils import (
    BLOCK_ADDR,
    CTRL_ADDR,
    DIGEST_ADDR,
    MAPPING,
    Request,
    RequestCovergroup,
    align,
)

ITERATIONS = int(os.getenv("ITERATIONS", 10))
SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")
VSC = os.getenv("VSC", "0")
VSC_FILE = os.getenv("VSC_FILE", "vsc.xml")

if cocotb.simulator.is_running():
    DATA_WIDTH = int(cocotb.top.DataWidth)
    ADDR_WIDTH = int(cocotb.top.AddrWidth)
    BLOCK_WIDTH = int(cocotb.top.BlockWidth)
    BYTE_ALIGN = int(cocotb.top.ByteAlign)
    DIGEST_WIDTH = int(cocotb.top.DigestWidth)

    ADDR_STEP: int = 8 if BYTE_ALIGN else 32

    DIGEST_REGS_ADDR: List[int] = [
        align(addr, ADDR_STEP) + DIGEST_ADDR
        for addr in range(0, DIGEST_WIDTH, DATA_WIDTH)
    ]

    BLOCK_REGS_ADDR: List[int] = [
        align(addr, ADDR_STEP) + BLOCK_ADDR
        for addr in range(0, BLOCK_WIDTH, DATA_WIDTH)
    ]

    VALID_REGS_ADDR: List[int] = DIGEST_REGS_ADDR + BLOCK_REGS_ADDR + [CTRL_ADDR]

    request: Request = Request(ADDR_WIDTH, DATA_WIDTH, ADDR_STEP)
    request_covergroup: RequestCovergroup = RequestCovergroup(
        ADDR_WIDTH,
        DATA_WIDTH,
        ADDR_STEP,
        BLOCK_REGS_ADDR,
        DIGEST_REGS_ADDR,
        VALID_REGS_ADDR,
    )


@cocotb.coroutine
async def init(dut):
    """Initialize input signals value"""

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


def overwwrite(prev_value: int, write_value: int, strobe: int) -> int:
    """Overwrite a register value with a new value"""

    exp_value: int = 0
    data: int = 0

    for b in range(0, DATA_WIDTH >> 3):
        data = write_value if strobe & (1 << b) else prev_value
        exp_value |= data & (0xFF << b * 8)

    return exp_value


def pseudowrite(
    prev_value: int, write_value: int, addr: int, strobe: int, err: bool
) -> int:
    """Simulate a write operation in the register interface based on the register previous value and request parameters"""

    # Return early if we know it's an invalid address
    if err:
        return 0

    # Function is split by address ranges
    if addr in DIGEST_REGS_ADDR:
        return prev_value

    elif addr in BLOCK_REGS_ADDR:
        return overwwrite(prev_value, write_value, strobe)

    elif addr == CTRL_ADDR:
        # If strobe[0] is not set, nothing is written
        if not (strobe & 0x1):
            return prev_value

        # Mask for control register
        ctrl_mask: int = 0b100001

        # If reset bit is written, register is cleared
        if (write_value >> 1) & 0x1:
            return 0

        return overwwrite(prev_value, write_value, strobe) & ctrl_mask


@cocotb.test()
async def toggle_reset(dut) -> None:
    """Toggle reset signal (sanity check)"""

    await init(dut)

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")
    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"


async def register_accesses(dut, id) -> None:
    """Register accesses with randomly contrained data"""

    # Randomize and sample the request
    request.randomize()
    request_covergroup.sample(request)

    # Gather request parameters
    data: int = request.data
    be: int = request.be
    addr: int = request.addr

    # Define expected results based on request parameters
    err: bool = addr not in VALID_REGS_ADDR
    valid: bool = addr in VALID_REGS_ADDR

    # Apply a random value to the read only digest register
    dut.digest_i.value = randbits(DIGEST_WIDTH)

    # Start clock and create Master interface
    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())
    master: Master = Master(dut, name=None, clock=dut.clk_i, mapping=MAPPING)

    # Read register before write operation
    prev_value = await master.read(address=addr)
    exp_value: int = pseudowrite(prev_value.value, data, addr, be, err)

    # Write request
    await master.write(address=addr, value=data, strobe=be)
    dut._log.debug(f"Write: {data:#x} at address {addr:#x} with byte enable {be:b}")

    # Wait next cycle for response
    await RisingEdge(dut.clk_i)

    # Check response status
    rsperr: bool = bool(dut.rsperror_o.value)
    rspvalid: bool = bool(dut.rspvalid_o.value)

    # Error and valid should never be asserted in the same cycle
    assert rsperr & rspvalid == False

    # Error response
    assert (
        rsperr == err
    ), f"Test {id}: Incorrect response error at {addr:#x}: expected {err}."

    # Valid response
    assert (
        rspvalid == valid
    ), f"Test {id}: Incorrect valid response at {addr:#x}: expected {valid}."

    # Read value back
    read_value = await master.read(address=addr)
    read_value = int(read_value.value) if valid else 0

    dut._log.debug(f"Read: {read_value:#x} at address {addr:#x}")

    # Compare read value and expected value
    assert read_value == exp_value, (
        f"Test {id}:",
        f"Expected {exp_value:#x} at address {addr:#x}, read {read_value:#x}",
    )

    await ClockCycles(dut.clk_i, 2)

    # Export coverage on last iteration
    if VSC == "1" and id == (ITERATIONS):
        vsc.write_coverage_db(f"{VSC_FILE}")
        dut._log.info(f"Coverage file written in {VSC_FILE}")


# Automatic tests generation depending on requested number of iterations
factory = TestFactory(register_accesses)
factory.add_option(name="id", optionlist=range(1, ITERATIONS + 1))
factory.generate_tests()


@pytest.mark.parametrize("DataWidth", ["16", "32", "64"])
@pytest.mark.parametrize("BlockWidth", ["512", "1024"])
@pytest.mark.parametrize("ByteAlign", ["1'b0", "1'b1"])
@pytest.mark.parametrize("DigestWidth", ["224", "256", "384", "512"])
def test_interface_regs(DataWidth, BlockWidth, ByteAlign, DigestWidth):
    """Run cocotb tests on sha1 registers for different combinations of parameters.

    Args:
            DataWidth:   Data bus width.
            BlockWidth:  Width of the block to compute.
            ByteAlign:   Whether we want an alignment on bytes or words.
            DigestWidth: Width of the final digest.

    """

    # skip test if there is an invalid combination of parameters
    if ByteAlign == "1'b0" and DataWidth == "16":
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
        extra_args = ["--trace", "--trace-structs", "--trace-fst"]

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
