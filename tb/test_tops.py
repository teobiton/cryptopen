# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import os
from secrets import choice
from string import printable
from typing import Dict, List, Union

import cocotb
import pytest
from cocotb.clock import Clock
from cocotb.regression import TestFactory
from cocotb.runner import Simulator, get_runner
from cocotb.triggers import ClockCycles, RisingEdge, Timer
from driver import Driver
from sha1.model.sha1_model import sha1
from sha2.model.sha256_model import sha256
from sha2.model.sha512_model import sha512

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

MAPPING: Dict[str, str] = {
    "reqdata": "sha_s_reqdata_i",
    "reqaddr": "sha_s_reqaddr_i",
    "reqvalid": "sha_s_reqvalid_i",
    "reqwrite": "sha_s_reqwrite_i",
    "reqready": "sha_s_reqready_o",
    "reqstrobe": "sha_s_reqstrobe_i",
    "rspready": "sha_s_rspready_i",
    "rspvalid": "sha_s_rspvalid_o",
    "rspdata": "sha_s_rspdata_o",
    "rsperror": "sha_s_rsperror_o",
}


def intblock(blocks: List[bytearray], index: int) -> int:
    return int.from_bytes(blocks[index], byteorder="big")


# Factory to build models on the fly
def core_factory(
    name: str, block_width: int, digest_width: int
) -> Union[sha1, sha256, sha512]:
    if name == "sha1":
        return sha1()
    elif name == "sha256":
        return sha256(digest_width=digest_width)
    elif name == "sha512":
        return sha512(digest_width=digest_width)
    else:
        return ValueError(f"Unsupported block width: {block_width}")


@cocotb.coroutine
async def init(dut):
    """Initialize input signals value"""

    dut.sha_s_reqdata_i.value = 0
    dut.sha_s_reqaddr_i.value = 0
    dut.sha_s_reqvalid_i.value = 0
    dut.sha_s_reqwrite_i.value = 0
    dut.sha_s_reqstrobe_i.value = 0
    dut.sha_s_rspready_i.value = 0

    dut.rst_ni.value = 0

    await Timer(1, units="ns")


@cocotb.test()
async def toggle_reset(dut) -> None:
    """Toggle reset signal (sanity check)"""

    await init(dut)

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"


@cocotb.test()
async def run_one_block_message(dut) -> None:
    """Write block and run algorithm for a one block message"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    # Instantiate driver to access registers
    driver: Driver = Driver(
        entity=dut,
        data_width=DATA_WIDTH,
        addr_width=ADDR_WIDTH,
        byte_align=BYTE_ALIGN,
        block_width=BLOCK_WIDTH,
        digest_width=DIGEST_WIDTH,
        bus_mapping=MAPPING,
    )

    message: str = "abc"

    # Instantiate Python model
    model = core_factory(dut.name, BLOCK_WIDTH, DIGEST_WIDTH)
    model.process(message)

    # Write block to registers
    block = intblock(model.blocks, 0)
    await driver.write_block(block=block)

    await RisingEdge(dut.clk_i)

    # Check if the core received the correct value
    assert dut.block.value == block

    # Enable algorithm by writing enable bit in control register
    await driver.enable()

    # Read valid bit in control register
    while True:
        core_done = await driver.read_valid()
        if core_done:
            break
        await RisingEdge(dut.clk_i)

    # Read digest value
    digest: str = f"{await driver.read_digest():x}"
    assert digest == model.digest().lstrip(
        "0"
    ), f"Expected digest {model.digest().lstrip('0')}, got {digest}"

    # Reset core
    await driver.reset()

    await RisingEdge(dut.clk_i)

    assert dut.idle == 1

    await ClockCycles(dut.clk_i, 2)

    assert dut.digest_valid == 0


@cocotb.test()
async def run_two_block_message(dut) -> None:
    """Write blocks and run algorithm for a two block message"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    # Instantiate driver to access registers
    driver: Driver = Driver(
        entity=dut,
        data_width=DATA_WIDTH,
        addr_width=ADDR_WIDTH,
        byte_align=BYTE_ALIGN,
        block_width=BLOCK_WIDTH,
        digest_width=DIGEST_WIDTH,
        bus_mapping=MAPPING,
    )

    messages = {
        512: "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
        1024: "abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu",
    }

    message: str = messages[BLOCK_WIDTH]

    # Instantiate Python model
    model = core_factory(dut.name, BLOCK_WIDTH, DIGEST_WIDTH)
    model.process(message)

    for cycle in range(len(model.blocks)):
        # Write block to registers
        block = intblock(model.blocks, cycle)
        await driver.write_block(block=block)

        await RisingEdge(dut.clk_i)

        # Check if the core received the correct value
        assert dut.block.value == block

        # Enable algorithm by writing enable bit in control register
        await driver.enable()

        # Read valid bit in control register
        while True:
            core_hold = await driver.read_hold()
            core_done = await driver.read_valid()

            if core_hold or core_done:
                break

            await RisingEdge(dut.clk_i)

    # Read digest value
    digest: str = f"{await driver.read_digest():x}"
    assert digest == model.digest().lstrip(
        "0"
    ), f"Expected digest {model.digest().lstrip('0')}, got {digest}"

    # Reset core
    await driver.reset()

    await RisingEdge(dut.clk_i)

    assert dut.idle == 1

    await ClockCycles(dut.clk_i, 2)

    assert dut.digest_valid == 0


async def run_random_message(dut, message) -> None:
    """Write blocks and run algorithm for random messages"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    # Instantiate driver to access registers
    driver: Driver = Driver(
        entity=dut,
        data_width=DATA_WIDTH,
        addr_width=ADDR_WIDTH,
        byte_align=BYTE_ALIGN,
        block_width=BLOCK_WIDTH,
        digest_width=DIGEST_WIDTH,
        bus_mapping=MAPPING,
    )

    # Instantiate Python model
    model = core_factory(dut.name, BLOCK_WIDTH, DIGEST_WIDTH)
    model.process(message)

    for cycle in range(len(model.blocks)):
        # Write block to registers
        block = intblock(model.blocks, cycle)
        await driver.write_block(block=block)

        await RisingEdge(dut.clk_i)

        # Check if the core received the correct value
        assert dut.block.value == block

        # Enable algorithm by writing enable bit in control register
        await driver.enable()

        # Read valid bit in control register
        while True:
            core_hold = await driver.read_hold()
            core_done = await driver.read_valid()

            if core_hold or core_done:
                break

            await RisingEdge(dut.clk_i)

    # Read digest value
    digest: str = f"{await driver.read_digest():x}"
    assert digest == model.digest().lstrip(
        "0"
    ), f"Expected digest {model.digest().lstrip('0')}, got {digest}"

    # Reset core
    await driver.reset()

    await RisingEdge(dut.clk_i)

    assert dut.idle == 1

    await ClockCycles(dut.clk_i, 2)

    assert dut.digest_valid == 0


factory = TestFactory(run_random_message)
messages: List[str] = [
    "".join(choice(printable) for _ in range(choice(range(5, 2000))))
    for _ in range(ITERATIONS)
]
factory.add_option(name="message", optionlist=messages)
factory.generate_tests()


@pytest.mark.parametrize("ip", ["sha1", "sha256", "sha512"])
def test_ip(ip):
    """Run cocotb tests on accelators IPs."""

    tests_dir: str = os.path.dirname(__file__)
    root_dir: str = os.path.abspath(os.path.join(tests_dir, ".."))
    rtl_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "hw", ip))
    itf_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "hw", "interface"))

    dut: str = ip
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = ip

    verilog_sources: List[str] = []

    with open(f"{rtl_dir}/Flist.{ip}") as flist:
        for f in flist:
            verilog_sources.append(os.path.join(root_dir, f))

    extra_args: List[str] = []

    if SIM == "verilator" and WAVES == "1":
        extra_args = ["--trace", "--trace-structs"]

    sim_build: str = os.path.join(tests_dir, f"{SIM_BUILD}", f"{dut}_sim_build")

    runner: Simulator = get_runner(simulator_name=SIM)

    runner.build(
        verilog_sources=verilog_sources,
        hdl_toplevel=toplevel,
        always=True,
        build_dir=sim_build,
        build_args=extra_args,
    )

    runner.test(hdl_toplevel=toplevel, test_module=module)
