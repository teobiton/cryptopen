# Copyright 2023 - cryptopen contributors
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

from interface.bus.master import Master
from interface.utils import CTRL_ADDR, DIGEST_ADDR, BLOCK_ADDR
from interface.utils import MAPPING

SIM = os.getenv("SIM", "verilator")
SIM_BUILD = os.getenv("SIM_BUILD", "sim_build")
WAVES = os.getenv("WAVES", "0")


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


@pytest.mark.parametrize("ip", ["sha1", "sha256", "sha512"])
def test_IP(ip):
    """Run cocotb tests on accelators IPs."""

    tests_dir: str = os.path.dirname(__file__)
    root_dir: str = os.path.abspath(os.path.join(tests_dir, ".."))
    rtl_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "hw", ip))
    itf_dir: str = os.path.abspath(os.path.join(tests_dir, "..", "hw", "interface"))

    dut: str = ip
    module: str = os.path.splitext(os.path.basename(__file__))[0]
    toplevel: str = ip

    verilog_sources: List[str] = [
        os.path.join(itf_dir, f"simple_reg_interface.sv"),
    ]

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
