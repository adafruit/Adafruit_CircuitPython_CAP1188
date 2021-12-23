# SPDX-FileCopyrightText: 2018 Carter Nelson for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
`adafruit_cap1188.cap1188`
====================================================

CircuitPython driver for the CAP1188 8-Key Capacitive Touch Sensor Breakout.

* Author(s): Carter Nelson, Jeremiah Rose, Jose David M.

Implementation Notes
--------------------

**Hardware:**

* `CAP1188 - 8-Key Capacitive Touch Sensor Breakout
  <https://www.adafruit.com/product/1602>`_  (Product ID: 1602)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

from micropython import const

try:
    from typing import Tuple, Union
except ImportError:
    pass

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CAP1188.git"


_CAP1188_MID = const(0x5D)
_CAP1188_PID = const(0x50)
_CAP1188_MAIN_CONTROL = const(0x00)
_CAP1188_GENERAL_STATUS = const(0x02)
_CAP1188_INPUT_STATUS = const(0x03)
_CAP1188_LED_STATUS = const(0x04)
_CAP1188_NOISE_FLAGS = const(0x0A)
_CAP1188_DELTA_COUNT = (
    const(0x10),
    const(0x11),
    const(0x12),
    const(0x13),
    const(0x14),
    const(0x15),
    const(0x16),
    const(0x17),
)
_CAP1188_SENSITIVTY = const(0x1F)
_CAP1188_AVERAGING = const(0x24)
_CAP1188_CAL_ACTIVATE = const(0x26)
_CAP1188_MULTI_TOUCH_CFG = const(0x2A)
_CAP1188_THESHOLD_1 = const(0x30)
_CAP1188_STANDBY_CFG = const(0x41)
_CAP1188_LED_LINKING = const(0x72)
_CAP1188_PRODUCT_ID = const(0xFD)
_CAP1188_MANU_ID = const(0xFE)
_CAP1188_REVISION = const(0xFF)


_SENSITIVITY = (128, 64, 32, 16, 8, 4, 2, 1)
_AVG = (1, 2, 4, 8, 16, 32, 64, 128)
_SAMP_TIME = ("320us", "640us", "1.28ms", "2.56ms")
_CYCLE_TIME = ("35ms", "70ms", "105ms", "140ms")


class CAP1188_Channel:
    # pylint: disable=protected-access
    """Helper class to represent a touch channel on the CAP1188. Not meant to
    be used directly."""

    def __init__(self, cap1188: "CAP1188", pin: int) -> None:
        self._cap1188 = cap1188
        self._pin = pin

    @property
    def value(self) -> bool:
        """Whether the pin is being touched or not."""
        return self._cap1188.touched() & (1 << self._pin - 1) != 0

    @property
    def raw_value(self) -> int:
        """The raw touch measurement."""
        return self._cap1188.delta_count(self._pin)

    @property
    def threshold(self) -> int:
        """The touch threshold value."""
        return self._cap1188._read_register(_CAP1188_THESHOLD_1 + self._pin - 1)

    @threshold.setter
    def threshold(self, value: int) -> None:
        value = int(value)
        if not 0 <= value <= 127:
            raise ValueError("Threshold value must be in range 0 to 127.")
        self._cap1188._write_register(_CAP1188_THESHOLD_1 + self._pin - 1, value)

    def recalibrate(self) -> None:
        """Perform a self recalibration."""
        self._cap1188.recalibrate_pins(1 << self._pin - 1)


class CAP1188:
    """CAP1188 driver base, must be extended for I2C/SPI interfacing."""

    def __init__(self) -> None:
        mid = self._read_register(_CAP1188_MANU_ID)
        if mid != _CAP1188_MID:
            raise RuntimeError(
                "Failed to find CAP1188! Manufacturer ID: 0x{:02x}".format(mid)
            )
        pid = self._read_register(_CAP1188_PRODUCT_ID)
        if pid != _CAP1188_PID:
            raise RuntimeError(
                "Failed to find CAP1188! Product ID: 0x{:02x}".format(pid)
            )
        self._channels = [None] * 8
        self._write_register(_CAP1188_LED_LINKING, 0xFF)  # turn on LED linking
        self._write_register(_CAP1188_MULTI_TOUCH_CFG, 0x00)  # allow multi touch
        self._write_register(0x2F, 0x10)  # turn off input-1-sets-all-inputs feature
        self.recalibrate()

    def __getitem__(self, key: int) -> CAP1188_Channel:
        pin = key
        index = key - 1
        if pin < 1 or pin > 8:
            raise IndexError("Pin must be a value 1-8.")
        if self._channels[index] is None:
            self._channels[index] = CAP1188_Channel(self, pin)
        return self._channels[index]

    @property
    def touched_pins(self) -> Tuple[bool, bool, bool, bool, bool, bool, bool, bool]:
        """A tuple of touched state for all pins."""
        touched = self.touched()
        return tuple(bool(touched >> i & 1) for i in range(8))

    def touched(self) -> int:
        """Return 8 bit value representing touch state of all pins."""
        # clear the INT bit and any previously touched pins
        current = self._read_register(_CAP1188_MAIN_CONTROL)
        self._write_register(_CAP1188_MAIN_CONTROL, current & ~0x01)
        # return only currently touched pins
        return self._read_register(_CAP1188_INPUT_STATUS)

    @property
    def sensitivity(self) -> int:
        """The sensitvity of touch detections. Range is 1 (least) to 128 (most)."""
        return _SENSITIVITY[self._read_register(_CAP1188_SENSITIVTY) >> 4 & 0x07]

    @sensitivity.setter
    def sensitivity(self, value: int) -> None:
        if value not in _SENSITIVITY:
            raise ValueError("Sensitivty must be one of: {}".format(_SENSITIVITY))
        value = _SENSITIVITY.index(value) << 4
        new_setting = self._read_register(_CAP1188_SENSITIVTY) & 0x8F | value
        self._write_register(_CAP1188_SENSITIVTY, new_setting)

    @property
    def averaging(self) -> int:
        """Samples that are taken for all active channels during the
        sensor cycle. All samples are taken consecutively on
        the same channel before the next channel is sampled
        and the result is averaged over the number of samples measured
        before  updating the measured results

        if CS1, CS2, and CS3 are sampled during the sensor cycle,
        and the AVG[2:0] bits are set to take 4 samples per channel,
        then the full sensor cycle will be:
        CS1, CS1, CS1, CS1, CS2, CS2, CS2, CS2, CS3, CS3, CS3, CS3.
        """

        register = self._read_register(_CAP1188_AVERAGING)

        return _AVG[register >> 4 & 0x07]

    @averaging.setter
    def averaging(self, value: int) -> None:
        if value not in _AVG:
            raise ValueError("Avg must be one of: {}".format(_AVG))
        register = self._read_register(_CAP1188_AVERAGING)
        register = register & 0x8F
        avg = _AVG.index(value)
        avg_value = register | avg << 4
        self._write_register(_CAP1188_AVERAGING, avg_value)

    @property
    def sample(self) -> str:
        """Determines the overall cycle time for all  measured  channels
        during normal operation. All measured channels are sampled at the
        beginning of the cycle time. If additional time is remaining, then
        the  device is placed into a lower power state for the remaining
        duration of the cycle."""

        register = self._read_register(_CAP1188_AVERAGING)

        return _SAMP_TIME[register >> 2 & 0x03]

    @sample.setter
    def sample(self, value: str) -> None:
        if value not in _SAMP_TIME:
            raise ValueError("Sample Time must be one of: {}".format(_SAMP_TIME))
        register = self._read_register(_CAP1188_AVERAGING)
        register = register & 0xF3
        samp_time = _SAMP_TIME.index(value)
        sample_value = register | samp_time << 2
        self._write_register(_CAP1188_AVERAGING, sample_value)

    @property
    def cycle(self) -> str:
        """The programmed cycle time is only maintained if
        the total averaging time for all samples is less
        than the programmed cycle. The AVG[2:0] bits will
        take priority so that if more samples are required
        than  would normally be allowed during the cycle
        time, the cycle time will be extended as necessary
        to accommodate the number of samples to be measured.
        """

        register = self._read_register(_CAP1188_AVERAGING)

        return _CYCLE_TIME[register & 0x03]

    @cycle.setter
    def cycle(self, value: str) -> None:
        if value not in _CYCLE_TIME:
            raise ValueError("Cycle Time must be one of: {}".format(_CYCLE_TIME))
        register = self._read_register(_CAP1188_AVERAGING)
        register = register & 0xFC
        cycle_time = _CYCLE_TIME.index(value)
        cycle_value = register | cycle_time
        self._write_register(_CAP1188_AVERAGING, cycle_value)

    @property
    def thresholds(self) -> Tuple[int, int, int, int, int, int, int, int]:
        """Touch threshold value for all channels."""
        return self.threshold_values()

    @thresholds.setter
    def thresholds(self, value: int) -> None:
        value = int(value)
        if not 0 <= value <= 127:
            raise ValueError("Threshold value must be in range 0 to 127.")
        self._write_block(_CAP1188_THESHOLD_1, bytearray((value,) * 8))

    def threshold_values(self) -> Tuple[int, int, int, int, int, int, int, int]:
        """Return tuple of touch threshold values for all channels."""
        return tuple(self._read_block(_CAP1188_THESHOLD_1, 8))

    def recalibrate(self) -> None:
        """Perform a self recalibration on all the pins."""
        self.recalibrate_pins(0xFF)

    def delta_count(self, pin: int) -> int:
        """Return the 8 bit delta count value for the channel."""
        if pin < 1 or pin > 8:
            raise IndexError("Pin must be a value 1-8.")
        # 8 bit 2's complement
        raw_value = self._read_register(_CAP1188_DELTA_COUNT[pin - 1])
        raw_value = raw_value - 256 if raw_value & 128 else raw_value
        return raw_value

    def recalibrate_pins(self, mask: int) -> None:
        """Recalibrate pins specified by bit mask."""
        self._write_register(_CAP1188_CAL_ACTIVATE, mask)

    def _read_register(self, address: int) -> int:
        """Return 8 bit value of register at address."""
        raise NotImplementedError

    def _write_register(self, address: int, value: int) -> None:
        """Write 8 bit value to register at address."""
        raise NotImplementedError

    def _read_block(self, start: int, length: int) -> bytearray:
        """Return byte array of values from start address to length."""
        raise NotImplementedError

    def _write_block(self, start: int, data: Union[bytearray, bytes]) -> None:
        """Write out data beginning at start address."""
        raise NotImplementedError
