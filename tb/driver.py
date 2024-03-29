# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from typing import Dict, List, Optional

from cocotb.handle import SimHandleBase

from interface.bus.master import Master


class Driver:
    """Driver

    This driver is used to control the dut by accessing registers only to read/write block data and enable the algorithm.

    """

    def __init__(
        self,
        entity: SimHandleBase,
        data_width: int,
        addr_width: int,
        byte_align: int,
        block_width: int,
        digest_width: int,
        block_addrs: List[int],
        digest_addrs: List[int],
        ctrl_addr: int,
        bus_mapping: Optional[Dict[str, str]] = None,
    ):
        self.entity = entity
        self.bus = Master(
            self.entity, name=None, clock=self.entity.clk_i, mapping=bus_mapping
        )

        self.data_width = data_width
        self.addr_width = addr_width
        self.byte_align = byte_align
        self.block_width = block_width
        self.digest_width = digest_width

        self.block_addrs: List[int] = block_addrs
        self.digest_addrs: List[int] = digest_addrs
        self.ctrl_addr: int = ctrl_addr

    async def write_block(self, block: int) -> None:
        mask = 2**self.data_width - 1

        for index, addr in enumerate(self.block_addrs):
            data = (block >> (self.data_width * index)) & mask
            await self.bus.write(value=data, address=addr)

    async def read_block(self) -> int:
        block: int = 0

        for index, addr in enumerate(self.block_addrs):
            data = await self.bus.read(address=addr)
            block |= data << (self.data_width * index)

        return block

    async def read_digest(self) -> int:
        digest: int = 0

        for index, addr in enumerate(self.digest_addrs):
            data = await self.bus.read(address=addr)
            digest |= data << (self.data_width * index)

        return digest

    async def enable(self, last_block=False) -> None:
        # write enable or last_block + enable
        value = 0x1 if not last_block else 0x21
        await self.bus.write(value=value, address=self.ctrl_addr)

    async def disable(self) -> None:
        await self.bus.write(value=0x0, address=self.ctrl_addr)

    async def reset(self) -> None:
        await self.bus.write(value=0x2, address=self.ctrl_addr)

    async def read_hold(self) -> int:
        ctrlreg = await self.bus.read(address=self.ctrl_addr)
        return ctrlreg & 0x8

    async def read_valid(self) -> int:
        ctrlreg = await self.bus.read(address=self.ctrl_addr)
        return ctrlreg & 0x10
