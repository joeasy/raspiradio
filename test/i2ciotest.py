#!/usr/bin/python
from smbus import SMBus
from time import sleep

bus = SMBus(1) # Port 1 used on REV2

while True:
   bus.write_byte(0x20,0x08)
   sleep(2)
   bus.write_byte(0x20,255)
   sleep(2)

#def set_bit(value, bit):
#    return value | (1<<bit)

#def clear_bit(value, bit):
#    return value & ~(1<<bit)

#io_port = 0b00000000

#print io_port

#io_port = set_bit(io_port,3)
#print io_port

#io_port = set_bit(io_port,0)
#print io_port

#io_port = clear_bit(io_port,3)
#print io_port
