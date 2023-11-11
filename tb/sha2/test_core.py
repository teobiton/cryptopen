import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer
from cocotb.runner import get_runner, Simulator

import os
import pytest
from secrets import choice
from string import ascii_lowercase
from typing import Dict, List

from lib2 import fsm, init, intblock, round_computation
from model.sha256 import sha256

SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")

if cocotb.simulator.is_running():
    BLOCK_WIDTH = int(cocotb.top.BlockWidth)
    DIGEST_WIDTH = int(cocotb.top.DigestWidth)


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
    model: sha256 = sha256(sha224=DIGEST_WIDTH == 224)
    model.process(message)

    # apply 512-bit block to block_i input
    # byte order is big endian because logic is reversed between python's lists and verilog logic
    dut.block_i.value = intblock(model.blocks, 0)
    dut.enable_hash_i.value = 1

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
    digest: str = f"{int(dut.sha_digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest(), f"Expected digest {model.digest()}, got {digest}"


@cocotb.test()
async def multi_blocks_message(dut) -> None:
    """Compute a multi-block message (N=2)"""

    await init(dut)

    cocotb.start_soon(Clock(dut.clk_i, period=10, units="ns").start())

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"

    message: str = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"

    # generate hash value from model
    model: sha256 = sha256(sha224=DIGEST_WIDTH == 224)
    model.process(message)

    for cycle in range(len(model.blocks)):
        # apply 512-bit block to block_i input
        # byte order is big endian because logic is reversed between python's lists and verilog logic
        dut.block_i.value = intblock(model.blocks, cycle)
        dut.enable_hash_i.value = 1

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

    digest: str = f"{int(dut.sha_digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest(), f"Expected digest {model.digest()}, got {digest}"


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
    message: str = "".join(choice(ascii_lowercase) for _ in range(1000))

    dut._log.info(f"Performing sha256 algorithm for message : {message}")

    # generate hash value from model
    model: sha256 = sha256(sha224=DIGEST_WIDTH == 224)
    model.process(message)

    for cycle in range(len(model.blocks)):
        # apply 512-bit block to block_i input
        # byte order is big endian because logic is reversed between python's lists and verilog logic
        dut.block_i.value = intblock(model.blocks, cycle)
        dut.enable_hash_i.value = 1

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

    digest: str = f"{int(dut.sha_digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest(), f"Expected digest {model.digest()}, got {digest}"


@pytest.mark.parametrize("DigestWidth", ["224", "256"])
def test_sha256_core(DigestWidth):
    tests_dir: str = os.path.dirname(__file__)
    hw_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "..", "hw"))
    sha_dir: str = os.path.abspath(os.path.join(hw_dir, "sha256"))

    dut: str = "sha256_core"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = "sha256_core"

    verilog_sources: List[str] = [
        os.path.join(sha_dir, f"{dut}.sv"),
    ]

    extra_args: List[str] = []

    if SIM == "verilator" and WAVES == "1":
        extra_args = ["--trace", "--trace-structs"]

    # 2 warnings disallow testbench to run, waive them for now
    extra_args.append("-Wno-WIDTH")

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
