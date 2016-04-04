# raspiradio
raspberry pi radio with spi display and i2c audio chip
project is still in very early phase and not usable

Installation Notes

- apt-get install git
- apt-get install lirc
- apt-get install python-pip
- apt-get install python-setuptools python-dev
- pip install WiringPi2
- pip install spidev
- git clone https://github.com/guyc/py-gaugette
- python setup.py install
- pip install evdev
- apt-get install python-mpd
- apt-get install python-pygame
- apt-get install libiw-dev
- pip install iwlib
- #apt-get install libsystemd-dev
- #git clone https://github.com/systemd/python-systemd
- #python setup.py install
- apt-get install python-dbus
- git clone https://github.com/abn/python-systemd-dbus
- python setup.py install

- modprobe fbtft_device name=adafruit22a rotate=270 speed=48000000 fps=50
- /etc/modules-load.d/fbtft.conf
- /etc/modprobe.d/fbtft.conf
- con2fbmap 1 1

Useful links
- http://sainsmart.tumblr.com/post/52849596106/diagramsainsmart-18-tft-lcd-modules-connect
- https://rhobobase.wordpress.com/2015/05/01/mini-screen/
- https://github.com/notro/fbtft/wiki
