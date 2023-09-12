import cocotb
from cocotb.triggers import Timer
from cocotb.runner import get_runner, Simulator

import os
import pytest
from random import getrandbits
from typing import Dict, List

ITERATIONS = int(os.getenv("ITERATIONS", 10))
SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")

from model.sha1 import left_rotate


@cocotb.test()
async def random_tests(dut) -> None:
    """Tests with random values"""

    POSITION: int = dut.Position.value

    in0: int = 0x0

    dut._log.info(f"Random tests with {ITERATIONS} iterations.")

    for idx in range(ITERATIONS):
        in0 = getrandbits(32)

        expected_rotl: int = left_rotate(in0, POSITION)

        dut.in0_i.value = in0

        await Timer(10, units="ns")

        rotl_o: int = int(dut.rotl_o.value)

        assert rotl_o == expected_rotl, (
            f"Index {idx}: "
            f"Expected Left rotate function output to be {expected_rotl:#x}, "
            f"got {rotl_o:#x}"
        )


@pytest.mark.parametrize("rot_position", [0, 16, 32, 48, 64])
def test_prim_rotl(rot_position):
    tests_dir: str = os.path.dirname(__file__)
    rtl_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "hw", "prim"))

    dut: str = "rotl"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = "prim_generic_rotl"

    verilog_sources: List[str] = [
        os.path.join(rtl_dir, f"{dut}.sv"),
    ]

    extra_args: List[str] = []

    if SIM == "verilator":
        extra_args = ["--trace", "--trace-structs"]

    parameters: Dict[str, int] = {}

    parameters["Position"] = rot_position

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
