# Copyright 2023 @ cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Driver for a simple bus interface

The interface is inspired from APB but simplified its size is generic
and thus not 100% compliant. The master is really simple and allows
read and write operations.

"""

from typing import Dict, List, Optional

from cocotb.clock import Clock
from cocotb.decorators import coroutine
from cocotb.triggers import RisingEdge
from cocotb.binary import BinaryValue
from cocotb.handle import SimHandleBase

from cocotb_bus.drivers import BusDriver


class Mapper(BusDriver):
    """Interface Mapper

    This class maps the bus signals to the actual entity signals.

    """

    signals: List[str] = [
        "reqdata",
        "reqaddr",
        "reqvalid",
        "reqwrite",
        "reqready",
        "reqstrobe",
        "rspready",
        "rspvalid",
        "rspdata",
        "rsperror",
    ]

    def __init__(
        self,
        entity: SimHandleBase,
        name: str,
        clock: Clock,
        mapping: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        self._signals = mapping if mapping is not None else self.signals

        BusDriver.__init__(self, entity, name, clock, **kwargs)

        # Drive requests signals to default values
        self.bus.reqdata.value.binstr = "0" * len(self.bus.reqdata)
        self.bus.reqaddr.value.binstr = "0" * len(self.bus.reqaddr)
        self.bus.reqvalid.setimmediatevalue(0)
        self.bus.reqwrite.setimmediatevalue(0)
        self.bus.reqstrobe.value.binstr = "0" * len(self.bus.reqstrobe)

        # Master is always ready
        self.bus.rspready.setimmediatevalue(1)

    def read(self, address: int):
        pass

    def write(self, address: int, value: int, strobe: int):
        pass


class Master(Mapper):
    """Master interface"""

    def __init__(
        self,
        entity: SimHandleBase,
        name: str,
        clock: Clock,
        mapping: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        # Workaround for an issue with Verilator/Cocotb (see https://github.com/cocotb/cocotb/issues/3259)
        # case_insensitive=False is needed otherwise the bus class is unusable
        Mapper.__init__(
            self, entity, name, clock, mapping, case_insensitive=False, **kwargs
        )

    def __len__(self) -> int:
        return 2 ** len(self.bus.address)

    @coroutine
    async def read(self, address: int) -> BinaryValue:
        """Issue a request to the bus and block until this comes back.

        Simulation time still progresses
        but syntactically it blocks.

        Args:
            address: The address to read from.
            sync: Wait for rising edge on clock initially.
                Defaults to True.

        Returns:
            The read data value.

        """

        await self._acquire_lock()

        await RisingEdge(self.clock)

        self.bus.reqaddr.value = address
        self.bus.reqwrite.value = 0
        self.bus.reqvalid.value = 1
        self.bus.reqstrobe.value = int("1" * len(self.bus.reqstrobe), 2)

        await RisingEdge(self.clock)

        self.bus.reqaddr.value.binstr = "0" * len(self.bus.reqaddr)
        self.bus.reqvalid.value = 0
        self.bus.reqstrobe.value = int("0" * len(self.bus.reqstrobe), 2)

        while True:
            if self.bus.rspvalid.value:
                break
            await RisingEdge(self.clock)

        # Get the response data
        data = self.bus.rspdata.value

        self._release_lock()
        return data

    @coroutine
    async def write(
        self, address: int, value: int, strobe: Optional[int] = None
    ) -> None:
        """Write request to the given address with the specified value.

        Args:
            address: The address to write to.
            value: The data value to write.

        """

        if strobe is None:
            strobe = int("1" * len(self.bus.reqstrobe), 2)

        await self._acquire_lock()

        # Apply values to bus
        await RisingEdge(self.clock)

        self.bus.reqaddr.value = address
        self.bus.reqdata.value = value
        self.bus.reqwrite.value = 1
        self.bus.reqvalid.value = 1
        self.bus.reqstrobe.value = strobe

        # Deassert write
        await RisingEdge(self.clock)

        self.bus.reqaddr.value.binstr = "0" * len(self.bus.reqaddr)
        self.bus.reqdata.value.binstr = "0" * len(self.bus.reqdata)
        self.bus.reqwrite.value = 0
        self.bus.reqvalid.value = 0
        self.bus.reqstrobe.value = int("0" * len(self.bus.reqstrobe), 2)

        self._release_lock()
