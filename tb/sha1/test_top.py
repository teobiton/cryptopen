import cocotb
from cocotb.triggers import Timer
from cocotb.runner import get_runner, Simulator

import os
from typing import List

from lib import init

ITERATIONS = int(os.getenv("ITERATIONS", 10))
SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")


@cocotb.test()
async def toggle_reset(dut) -> None:
    """Toggle reset signal (sanity check)"""

    await init(dut)

    # Turn off reset
    dut.rst_ni.value = 1

    await Timer(35, units="ns")

    assert dut.rst_ni.value == 1, f"{dut.name} is still under reset"


def test_sha_toplevel():
    tests_dir: str = os.path.dirname(__file__)
    hw_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "..", "hw"))
    sha_dir: str = os.path.abspath(os.path.join(hw_dir, "sha1"))
    interface_dir: str = os.path.abspath(os.path.join(hw_dir, "interface"))

    dut: str = "sha1"
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = "sha1"

    verilog_sources: List[str] = [
        os.path.join(sha_dir, f"{dut}.sv"),
        os.path.join(interface_dir, "simple_reg_interface.sv"),
    ]

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
