from typing import Callable

from pymodbus.datastore import ModbusSequentialDataBlock


class WriteCallbackDataBlock(ModbusSequentialDataBlock):
    """Sequential datablock that fires a callback whenever values are written."""

    def __init__(self, address: int, values: list, write_callback: Callable | None = None):
        super().__init__(address, values)
        self._write_callback = write_callback

    def setValues(self, address: int, values: list) -> None:
        super().setValues(address, values)
        if self._write_callback:
            self._write_callback(address, values)
