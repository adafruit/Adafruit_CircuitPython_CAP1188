# The MIT License (MIT)
#
# Copyright (c) 2018 Carter Nelson for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_cap1188.cap1188`
====================================================

CircuitPython driver for the CAP1188 8-Key Capacitive Touch Sensor Breakout. 

* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* `CAP1188 - 8-Key Capacitive Touch Sensor Breakout <https://www.adafruit.com/product/1602>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
  
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

from micropython import const

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CAP1188.git"

# pylint: disable=bad-whitespace
CAP1188_MAIN_CONTROL        = const(0x00)
CAP1188_GENERAL_STATUS      = const(0x02)
CAP1188_INPUT_STATUS        = const(0x03)
CAP1188_LED_STATUS          = const(0x04)
CAP1188_NOISE_FLAGS         = const(0x0A)
CAP1188_DELTA_COUNT         =(const(0x10),
                              const(0x11),
                              const(0x12),
                              const(0x13),
                              const(0x14),
                              const(0x15),
                              const(0x16),
                              const(0x17))
CAP1188_CAL_ACTIVATE        = const(0x26)
CAP1188_MULTI_TOUCH_CFG     = const(0x2A)
CAP1188_STANDBY_CFG         = const(0x41)
CAP1188_LED_LINKING         = const(0x72)
CAP1188_PRODUCT_ID          = const(0xFD)
CAP1188_MANU_ID             = const(0xFE)
CAP1188_REVISION            = const(0xFF)
# pylint: enable=bad-whitespace

class CAP1188_Channel:
    """Helper class to represent a touch channel on the CAP1188. Not meant to
    be used directly."""
    def __init__(self, cap1188, pin):
        self._cap1188 = cap1188
        self._pin = pin

    @property
    def value(self):
        """Whether the pin is being touched or not."""
        return self._cap1188.touched() & (1 << self._pin - 1) != 0
        
    @property
    def raw_value(self):
        """The raw touch measurement."""
        return self._cap1188._delta_count(self._pin)

    def recalibrate(self):
        """Perform a self recalibration."""
        self._cap1188._recalibrate_pins(1 << self._pin - 1)
            

class CAP1188:
    """CAP1188 driver base, must be extended for I2C/SPI interfacing."""
    def __init__(self):
        self._channels = [None]*8
        self._write_register(CAP1188_LED_LINKING, 0xFF)     # turn on LED linking
        self._write_register(CAP1188_MULTI_TOUCH_CFG, 0x00) # allow multi touch
        self.recalibrate()

    def __getitem__(self, key):
        pin = key 
        index = key - 1
        if pin < 1 or pin > 8:
            raise IndexError('Pin must be a value 1-8.')
        if self._channels[index] is None:
            self._channels[index] = CAP1188_Channel(self, pin)
        return self._channels[index]

    @property
    def product_id(self):
        """The product ID."""
        return self._read_register(CAP1188_PRODUCT_ID)

    @property
    def manufacturer_id(self):
        """The manufacturer ID."""
        return self._read_register(CAP1188_REVISION)

    @property
    def revision(self):
        """The revision number."""
        return self._read_register(CAP1188_MANU_ID)

    @property
    def touched_pins(self):
        """A tuple of touched state for all pins."""
        touched = self.touched()
        return tuple([bool(touched >> i & 0x01) for i in range(8)])    

    def touched(self):
        """Return 8 bit value representing touch state of all pins."""
        # clear the INT bit and any previously touched pins
        current = self._read_register(CAP1188_MAIN_CONTROL)
        self._write_register(CAP1188_MAIN_CONTROL, current & ~0x01)
        # return only currently touched pins
        return self._read_register(CAP1188_INPUT_STATUS)

    def recalibrate(self):
        """Perform a self recalibration on all the pins."""
        self._recalibrate_pins(0xFF)

    def _delta_count(self, pin):
        """Return the 8 bit delta count value for the channel."""
        if pin < 1 or pin > 8:
            raise IndexError('Pin must be a value 1-8.') 
        return self._read_register(CAP1188_DELTA_COUNT[pin-1])

    def _recalibrate_pins(self, mask):
        self._write_register(CAP1188_CAL_ACTIVATE, mask)

    def _read_register(self, address):
        """Return 8 bit value of register at address."""
        raise NotImplementedError

    def _write_register(self, address, value):
        """Write 8 bit value to registter at address."""
        raise NotImplementedError
