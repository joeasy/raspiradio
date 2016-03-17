# raspiradio
raspberry pi radio with spi display and i2c audio chip
project is still in very early phase and not usable

Installation Notes

- apt-get install python-pygame
- apt-get install python-dev
- apt-get install libiw-dev
- pip install iwlib
- modprobe fbtft_device name=adafruit22a rotate=270 speed=48000000 fps=50
- /etc/modules-load.d/fbtft.conf
- /etc/modprobe.d/fbtft.conf
- con2fbmap 1 1
