import cocotb
from cocotb.triggers import Timer
from cocotb.runner import get_runner, Simulator

import os
from random import getrandbits
from typing import List

ITERATIONS = int(os.getenv("ITERATIONS", 10))
SIM = os.getenv("SIM", "verilator")

from model.sha1 import ch


@cocotb.test()
async def directed_tests(dut) -> None:
    """Directed tests with explicit values"""

    in0: int = 0xFFFF_F000
    in1: int = 0x000F_FFFF
    in2: int = 0xF0F0_F0F0

    expected_ch: int = 0xF0FF_0000

    dut.in0_i.value = in0
    dut.in1_i.value = in1
    dut.in2_i.value = in2

    await Timer(10, units="ns")

    ch_o: int = int(dut.ch_o.value)

    assert ch_o == expected_ch, (
        f"Expected Choose function output to be {expected_ch:#x}, " f"got {ch_o:#x}"
    )


@cocotb.test()
async def random_tests(dut) -> None:
    """Tests with random values"""

    in0: int = 0x0
    in1: int = 0x0
    in2: int = 0x0

    dut._log.info(f"Random tests with {ITERATIONS} iterations.")

    for idx in range(ITERATIONS):
        in0 = getrandbits(32)
        in1 = getrandbits(32)
        in2 = getrandbits(32)

        expected_ch: int = ch(in0, in1, in2)

        dut.in0_i.value = in0
        dut.in1_i.value = in1
        dut.in2_i.value = in2

        await Timer(10, units="ns")

        ch_o: int = int(dut.ch_o.value)

        assert ch_o == expected_ch, (
            f"Index {idx}: "
            f"Expected Choose function output to be {expected_ch:#x}, "
            f"got {ch_o:#x}"
        )


def test_prim_ch():
    tests_dir: str = os.path.dirname(__file__)
    rtl_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "hw", "prim"))

    dut: str = "ch"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = "prim_generic_ch"

    verilog_sources: List[str] = [
        os.path.join(rtl_dir, f"{dut}.sv"),
    ]

    extra_args: List[str] = []

    if SIM == "verilator":
        extra_args = ["--trace", "--trace-structs"]

    sim_build: str = os.path.join(tests_dir, f"{dut}_sim_build")

    runner: Simulator = get_runner(simulator_name=SIM)

    runner.build(
        verilog_sources=verilog_sources,
        hdl_toplevel=toplevel,
        always=True,
        build_dir=sim_build,
        build_args=extra_args,
    )

    runner.test(hdl_toplevel=toplevel, test_module=module)
