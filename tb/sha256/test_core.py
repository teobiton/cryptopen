import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer
from cocotb.runner import get_runner, Simulator

from enum import Enum
import os
from typing import List

from model.sha256 import sha256

SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")

if cocotb.simulator.is_running():
    BLOCK_WIDTH = int(cocotb.top.BlockWidth)
    DIGEST_WIDTH = int(cocotb.top.DigestWidth)


class fsm(Enum):
    IDLE = 0x0
    HASHING = 0x1
    HOLD = 0x2
    DONE = 0x3


@cocotb.coroutine
async def init(dut):
    """Initialize input signals value"""

    dut.block_i.value = 0
    dut.enable_hash_i.value = 0
    dut.rst_hash_i.value = 0

    dut.rst_ni.value = 0

    await Timer(1, units="ns")


def _round_computation(dut):
    values = [
        int(dut.a_q.value),
        int(dut.b_q.value),
        int(dut.c_q.value),
        int(dut.d_q.value),
        int(dut.e_q.value),
        int(dut.f_q.value),
        int(dut.g_q.value),
        int(dut.h_q.value),
    ]

    return " ".join(format(x, "08x") for x in values)


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
    model: sha256 = sha256()
    model.process(message)

    # apply 512-bit block to block_i input
    # byte order is big endian because logic is reversed between python's lists and verilog logic
    dut.block_i.value = int.from_bytes(model._pre_processing(message), byteorder="big")
    dut.enable_hash_i.value = 1

    # Wait until hash is done
    while True:
        roundcntr = int(dut.round_cntr_q.value)
        dut._log.debug(
            f"Round {roundcntr}:\n"
            f"Hardware : {_round_computation(dut)}\n"
            f"Model    : {model._round_computations[roundcntr]}\n"
        )

        if dut.digest_valid.value:
            dut.enable_hash_i.value = 0
            break
        await RisingEdge(dut.clk_i)

    digest: str = f"{int(dut.sha_digest_o.value):x}"

    # Compare hash values at the end of current cycle
    assert digest == model.digest(), f"Expected digest {model.digest()}, got {digest}"


def test_sha256_core():
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
