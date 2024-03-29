# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import os
from secrets import choice
from string import printable
from typing import Dict, List, Tuple, Union

import cocotb
import pytest
from cocotb.clock import Clock
from cocotb.runner import Simulator, get_runner
from cocotb.triggers import ClockCycles, RisingEdge, Timer
from lib2 import fsm, init, intblock, round_computation
from model.sha256_model import sha256
from model.sha512_model import sha512

SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")

if cocotb.simulator.is_running():
    BLOCK_WIDTH = int(cocotb.top.BlockWidth)
    DIGEST_WIDTH = int(cocotb.top.DigestWidth)


# Factory to build models on the fly
def core_factory(block_width, digest_width) -> Union[sha256, sha512]:
    if block_width == 1024:
        return sha512(digest_width=digest_width)
    elif block_width == 512:
        return sha256(digest_width=digest_width)
    else:
        return ValueError(f"Unsupported block width: {block_width}")


@cocotb.test()
async def toggle_reset(dut) -> None:
    """Toggle reset signal (sanity check)"""

    await init(dut)

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"


@cocotb.test()
async def fsm_transition(dut) -> None:
    """Test finite state machine valid transitions"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    assert fsm(dut.current_state.value) == fsm.IDLE

    # Turn off reset
    dut.rst_ni.value = 1
    await Timer(35, units="ns")
    assert fsm(dut.current_state.value) == fsm.IDLE

    # Enable hashing
    dut.enable_hash_i.value = 1
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.HASHING

    # Disable hashing
    dut.enable_hash_i.value = 0
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.HOLD

    # Enable hashing
    dut.enable_hash_i.value = 1
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.HASHING

    # Reset hashing
    dut.enable_hash_i.value = 0
    dut.rst_hash_i.value = 1
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.IDLE

    # Enable hashing
    dut.rst_hash_i.value = 0
    dut.enable_hash_i.value = 1
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.HASHING

    # Disable hashing
    dut.enable_hash_i.value = 0
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.HOLD

    # Reset hashing
    dut.rst_hash_i.value = 1
    await ClockCycles(dut.clk_i, 5)
    assert fsm(dut.current_state.value) == fsm.IDLE


@cocotb.test()
async def one_block_message(dut) -> None:
    """Compute a one block message"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    message: str = "abc"

    # generate hash value from model
    model = core_factory(BLOCK_WIDTH, DIGEST_WIDTH)
    model.process(message)

    # apply 512-bit block to block_i input
    # byte order is big endian because logic is reversed between python's lists and verilog logic
    dut.block_i.value = intblock(model.blocks, 0)
    dut.enable_hash_i.value = 1
    # signal last block since its a one block message
    dut.last_block_i.value = 1

    # Wait until hash is done
    while True:
        roundcntr = int(dut.round_cntr_q.value)
        dut._log.debug(
            f"Round {roundcntr}:\n"
            f"Hardware : {round_computation(dut)}\n"
            f"Model    : {model.round_computations[roundcntr]}\n"
        )

        if dut.round_done.value:
            dut.enable_hash_i.value = 0
            break
        await RisingEdge(dut.clk_i)

    await RisingEdge(dut.clk_i)
    digest: str = f"{int(dut.digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest().lstrip(
        "0"
    ), f"Expected digest {model.digest().lstrip('0')}, got {digest}"


@cocotb.test()
async def multi_blocks_message(dut) -> None:
    """Compute a multi-block message (N=2)"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    messages = {
        512: "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
        1024: "abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu",
    }

    message: str = messages[BLOCK_WIDTH]

    # generate hash value from model
    model = core_factory(BLOCK_WIDTH, DIGEST_WIDTH)
    model.process(message)

    for cycle in range(len(model.blocks)):
        # apply 512-bit block to block_i input
        # byte order is big endian because logic is reversed between python's lists and verilog logic
        dut.block_i.value = intblock(model.blocks, cycle)
        dut.enable_hash_i.value = 1
        # signal last block at last block
        dut.last_block_i.value = cycle == (len(model.blocks) - 1)

        # Wait until hash is done
        while True:
            roundcntr = int(dut.round_cntr_q.value)
            dut._log.debug(
                f"Round {roundcntr}:\n"
                f"Hardware : {round_computation(dut)}\n"
                f"Model    : {model.round_computations[64*cycle+roundcntr]}\n"
            )

            if dut.round_done.value or dut.digest_valid.value:
                dut.enable_hash_i.value = 0
                await ClockCycles(dut.clk_i, 3)
                break
            await RisingEdge(dut.clk_i)

    digest: str = f"{int(dut.digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest().lstrip(
        "0"
    ), f"Expected digest {model.digest().lstrip('0')}, got {digest}"


@cocotb.test()
async def long_random_message(dut) -> None:
    """Compute a long random message"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    # Compute a random message
    message: str = "".join(choice(printable) for _ in range(1000))

    dut._log.info(f"Performing sha256 algorithm for message : {message}")

    # generate hash value from model
    model = core_factory(BLOCK_WIDTH, DIGEST_WIDTH)
    model.process(message)

    for cycle in range(len(model.blocks)):
        # apply 512-bit block to block_i input
        # byte order is big endian because logic is reversed between python's lists and verilog logic
        dut.block_i.value = intblock(model.blocks, cycle)
        dut.enable_hash_i.value = 1
        # signal last block at last block
        dut.last_block_i.value = cycle == (len(model.blocks) - 1)

        # Wait until hash is done
        while True:
            roundcntr = int(dut.round_cntr_q.value)
            dut._log.debug(
                f"Round {roundcntr}:\n"
                f"Hardware : {round_computation(dut)}\n"
                f"Model    : {model.round_computations[64*cycle+roundcntr]}\n"
            )

            if dut.round_done.value or dut.digest_valid.value:
                dut.enable_hash_i.value = 0
                await ClockCycles(dut.clk_i, 3)
                break
            await RisingEdge(dut.clk_i)

    digest: str = f"{int(dut.digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest().lstrip(
        "0"
    ), f"Expected digest {model.digest().lstrip('0')}, got {digest}"


@pytest.mark.parametrize("DigestWidth", ["224", "256", "384", "512"])
@pytest.mark.parametrize("core", ["sha256", "sha512"])
def test_sha256_core(core, DigestWidth):
    # skip test if there is an invalid combination of parameters
    if core == "sha256" and DigestWidth in ["384", "512"]:
        pytest.skip(f"Invalid combination: core = {core} and DataWidth = {DigestWidth}")

    tests_dir: str = os.path.dirname(__file__)
    hw_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "..", "hw"))
    sha_dir: str = os.path.abspath(os.path.join(hw_dir, core))

    dut: str = f"{core}_core"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = f"{core}_core"

    verilog_sources: List[str] = [
        os.path.join(sha_dir, f"{dut}.sv"),
    ]

    extra_args: List[str] = []

    if SIM == "verilator" and WAVES == "1":
        extra_args = ["--trace", "--trace-structs", "--trace-fst"]

    parameters: Dict[str, str] = {}

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
