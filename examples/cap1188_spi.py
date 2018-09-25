import board
import busio
from digitalio import DigitalInOut, Direction
from adafruit_cap1188.spi import CAP1188_SPI

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs = DigitalInOut(board.D10)

cap = CAP1188_SPI(spi, cs)

while True:
    for i in range(1, 9):
        if cap[i].value:
            print("Pin {} touched!".format(i))