# SPDX-FileCopyrightText: 2018 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_cap1188.spi`
====================================================

CircuitPython SPI driver for the CAP1188 8-Key Capacitive Touch Sensor Breakout.

* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* `CAP1188 - 8-Key Capacitive Touch Sensor Breakout
  <https://www.adafruit.com/product/1602>`_ (Product ID: 1602)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

from adafruit_bus_device import spi_device
from micropython import const
from adafruit_cap1188.cap1188 import CAP1188

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CAP1188.git"

_CAP1188_SPI_SET_ADDR = const(0x7D)
_CAP1188_SPI_WRITE_DATA = const(0x7E)
_CAP1188_SPI_READ_DATA = const(0x7F)

try:
    from typing import Union
    from busio import SPI
    from digitalio import DigitalInOut
except ImportError:
    pass


class CAP1188_SPI(CAP1188):
    """Driver for the CAP1188 connected over SPI."""

    def __init__(self, spi: SPI, cs: DigitalInOut) -> None:
        self._spi = spi_device.SPIDevice(spi, cs)
        self._buf = bytearray(4)
        super().__init__()

    def _read_register(self, address: int) -> int:
        # pylint: disable=no-member
        """Return 8 bit value of register at address."""
        self._buf[0] = _CAP1188_SPI_SET_ADDR
        self._buf[1] = address
        self._buf[2] = _CAP1188_SPI_READ_DATA
        with self._spi as spi:
            spi.write_readinto(self._buf, self._buf)
        return self._buf[3]

    def _write_register(self, address: int, value: int) -> None:
        # pylint: disable=no-member
        """Write 8 bit value to registter at address."""
        self._buf[0] = _CAP1188_SPI_SET_ADDR
        self._buf[1] = address
        self._buf[2] = _CAP1188_SPI_WRITE_DATA
        self._buf[3] = value
        with self._spi as spi:
            spi.write(self._buf)

    def _read_block(self, start: int, length: int) -> bytearray:
        # pylint: disable=no-member
        """Return byte array of values from start address to length."""
        self._buf[0] = _CAP1188_SPI_SET_ADDR
        self._buf[1] = start
        self._buf[2] = _CAP1188_SPI_READ_DATA
        result = bytearray((_CAP1188_SPI_READ_DATA,) * length)
        with self._spi as spi:
            spi.write(self._buf, end=3)
            spi.write_readinto(result, result)
        return result

    def _write_block(self, start: int, data: Union[bytearray, bytes]) -> None:
        # pylint: disable=no-member
        """Write out data beginning at start address."""
        self._buf[0] = _CAP1188_SPI_SET_ADDR
        self._buf[1] = start
        with self._spi as spi:
            spi.write(self._buf, end=2)
            self._buf[0] = _CAP1188_SPI_WRITE_DATA
            for value in data:
                self._buf[1] = value
                spi.write(self._buf, end=2)
