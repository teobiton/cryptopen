# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import List

import cocotb
from cocotb.triggers import Timer


class fsm(Enum):
    IDLE = 0x0
    HASHING = 0x1
    HOLD = 0x2
    DONE = 0x3


async def init(dut):
    """Initialize input signals value"""

    dut.block_i.value = 0
    dut.enable_hash_i.value = 0
    dut.rst_hash_i.value = 0

    dut.rst_ni.value = 0

    await Timer(1, units="ns")


def intblock(blocks: List[bytearray], index: int) -> int:
    return int.from_bytes(blocks[index], byteorder="big")


def round_computation(dut):
    values = [
        int(dut.a_q.value),
        int(dut.b_q.value),
        int(dut.c_q.value),
        int(dut.d_q.value),
        int(dut.e_q.value),
    ]

    return " ".join(format(x, "08x") for x in values)
