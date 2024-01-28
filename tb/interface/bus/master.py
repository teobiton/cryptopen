# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Driver for a simple bus interface

The interface is inspired from APB but simplified its size is generic
and thus not 100% compliant. The master is really simple and allows
read and write operations.

"""

from typing import Dict, List, Optional

from cocotb.types import LogicArray
from cocotb.clock import Clock
from cocotb.handle import SimHandleBase
from cocotb.triggers import RisingEdge


def build_sig_attr_dict(signals):
    """Handle signals mapping provided by user or return generic one"""
    if isinstance(signals, dict):
        return signals
    return {sig: sig for sig in signals}


class Bus:
    """Bus

    A bus is just a simple interface between actual signals of the bus implementation and
    protocol generic names.

    """

    def __init__(self, entity, signals):
        """
        Args:
            entity: instance to the entity containing the bus.
            signals (list or dict): In the case of an object that has the same attribute names
                as the signal names of the bus, the signal* argument can be a list of those names.
                When the object has different attribute names, the signals argument should be
                a dict that maps bus attribute names to object signal names.
        """
        self._entity = entity
        self._signals = {}
        for attr_name, sig_name in build_sig_attr_dict(signals).items():
            signame = sig_name
            self._add_signal(attr_name, signame)

    def _add_signal(self, attr_name, signame):
        handle = getattr(self._entity, signame)
        setattr(self, attr_name, handle)
        self._signals[attr_name] = getattr(self, attr_name)


class SimpleMapper:
    """Simple Interface Mapper

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
        mapping: Optional[Dict[str, str]] = None,
    ):
        self._signals = mapping if mapping is not None else self.signals

        self.bus: Bus = Bus(entity, self._signals)

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


class SimpleMaster(SimpleMapper):
    """Simple Master interface"""

    def __init__(
        self,
        entity: SimHandleBase,
        clock: Clock,
        mapping: Optional[Dict[str, str]] = None,
    ):
        self.clock: Clock = clock
        SimpleMapper.__init__(self, entity, mapping)

    def __len__(self) -> int:
        return 2 ** len(self.bus.address)

    async def read(self, address: int) -> LogicArray:
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
            if self.bus.rspvalid.value or self.bus.rsperror.value:
                break
            await RisingEdge(self.clock)

        # Get the response data
        data = self.bus.rspdata.value

        self._release_lock()
        return data

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
