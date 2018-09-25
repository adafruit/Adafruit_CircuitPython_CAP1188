import board
import busio
from adafruit_cap1188.i2c import CAP1188_I2C

i2c = busio.I2C(board.SCL, board.SDA)

cap = CAP1188_I2C(i2c)

while True:
    for i in range(1, 9):
        if cap[i].value:
            print("Pin {} touched!".format(i))