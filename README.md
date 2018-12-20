# Roomba

This is repository for project that is about complete replacement of Roomba 581 control system by custom-made system.

Consists:

- Li-ion 3S BMS system, ensures safety of 18650 recycled batteries, balance and monitor them and communicate over I2C(TWI); it is located in separate repository: https://github.com/Zbysekz/3S_BMS

- Motherboard: collect data from sensors and communicate over I2C (TWI)

- Raspberry Pi 3B : The top of the system where python scripts are running and controls the vehicle


All schematics for PCBs can be found on EasyEDA (online tool)
https://easyeda.com/zbysekzapadlik/roomba
