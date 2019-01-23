import smbus2
import crc8
from sys import stdout
from time import sleep

bus = smbus2.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

ADDR_MOTHERBOARD = 0x27      #7 bit address (will be left shifted to add the read write bit)
ADDR_BMS = 0x28

sleep(1)
a = bus.read_byte_data(ADDR_BMS,2)

print(type(a))
print(a)
print(bus.read_byte_data(ADDR_BMS,2))
print(bus.read_byte_data(ADDR_BMS,2))
print(bus.read_byte_data(ADDR_BMS,2))
print(bus.read_byte_data(ADDR_BMS,2))