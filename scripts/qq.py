#!/usr/bin/python3

import smbus2

from sys import stdout
from time import sleep

bus = smbus2.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

ADDR_MOTHERBOARD = 0x27      #7 bit address (will be left shifted to add the read write bit)

print(bus.read_byte_data(ADDR_MOTHERBOARD,200))
sleep(0.5)
try:
    while(1):
        
        print(bus.read_byte_data(ADDR_MOTHERBOARD,7))
        sleep(0.1)
               
except KeyboardInterrupt:
    stdout.write("\n") # move the cursor to the next line
