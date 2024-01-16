# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List

import vsc

# Base addresses
CTRL_ADDR = 0x000
BLOCK_ADDR = 0x100
DIGEST_ADDR = 0x200


MAPPING: Dict[str, str] = {
    "reqdata": "reqdata_i",
    "reqaddr": "reqaddr_i",
    "reqvalid": "reqvalid_i",
    "reqwrite": "reqwrite_i",
    "reqready": "reqready_o",
    "reqstrobe": "reqstrobe_i",
    "rspready": "rspready_i",
    "rspvalid": "rspvalid_o",
    "rspdata": "rspdata_o",
    "rsperror": "rsperror_o",
}


def align(addr: int, step: int):
    return int(addr / step)


@vsc.randobj
class Request(object):
    def __init__(self, addr_width: int, data_width: int, step: int):
        self.addr = vsc.rand_bit_t(addr_width)
        self.data = vsc.rand_bit_t(data_width)
        self.be = vsc.rand_bit_t(data_width >> 3)
        self.step = step

    @vsc.constraint
    def addr_c(self):
        self.addr <= 0x2FF
        self.addr % self.step == 0


@vsc.covergroup
class RequestCovergroup(object):
    def __init__(
        self,
        addr_width: int,
        data_width: int,
        step: int,
        block_addrs: List[int],
        digest_addrs: List[int],
        valid_addrs: List[int],
    ):
        # Define the parameters accepted by the sample function
        self.with_sample(dict(req=Request(addr_width, data_width, step)))

        invalid_addrs: List[int] = [
            addr for addr in range(0x000, 0x2FF, step) if addr not in valid_addrs
        ]

        self.addr_cp = vsc.coverpoint(
            self.req.addr,
            bins={
                "CtrlRegAddr": vsc.bin(0x00),
                "BlockRegsAddr": vsc.bin(*block_addrs),
                "DigestRegsAddr": vsc.bin(*digest_addrs),
                "Other": vsc.bin(*invalid_addrs),
            },
        )

        self.be_cp = vsc.coverpoint(
            self.req.be, bins={"ByteEnable": vsc.bin([0x0, 0xFF])}
        )
