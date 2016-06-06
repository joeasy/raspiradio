# raspiradio
raspberry pi radio with spi display and i2c audio chip
project is still in very early phase and not usable

# Installation Notes

- apt-get install git
- apt-get install lirc
- apt-get install python-pip
- apt-get install python-setuptools python-dev
- pip install WiringPi2
- pip install spidev
- git clone https://github.com/guyc/py-gaugette
- python setup.py install
- pip install evdev
- apt-get install mpd
- apt-get install mpc
- apt-get install python-mpd
- apt-get install python-pygame
- apt-get install libiw-dev
- apt-get install i2c-tools
- apt-get install python-smbus
- apt-get install libi2c-dev
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
- /etc/modprobe.d/alsa-blacklist.conf
- con2fbmap 1 1

- apt-get install libssl-dev libavahi-client-dev libasound2-dev avahi-daemon
- git clone https://github.com/abrasive/shairport.git
- cd shairport
- ./configure
- make
- make install
- cp scripts/debian/init.d/shairport /etc/init.d/
- cp scripts/debian/default/shairport /etc/default/
- systemctl enable shairport
- systemctl start shairport

# Useful links
- http://sainsmart.tumblr.com/post/52849596106/diagramsainsmart-18-tft-lcd-modules-connect
- https://rhobobase.wordpress.com/2015/05/01/mini-screen/
- https://github.com/notro/fbtft/wiki

# GPIO Asignment

| GPIO Number |  Usage              | Comment              |
|-------------|---------------------|----------------------|
|   2         | I2C SDA             |                      |
|   3         | I2C SCL             |                      |
|   4         | encoder switch      |    unused in Yamaha  |
|   5         | unused              |                      |
|   6         | unused              |                      |
|   7         | SPI_CE1             |    free              |
|   8         | SPI_CE0             |    Display           |
|   9         | SPI_MISO            |    Display           |
|   10        | SPI_MOSI            |    Display           |
|   11        | SPI_CLK             |    Display           |
|   12        | unused              |                      |
|   13        | unused              |                      |
|   14        | TXD                 |                      |
|   15        | RXD                 |                      |
|   16        | unused              |                      |
|   17        | LIRC IR Reciver     |                      |
|   18        | BCK I2S audio       |                      |
|   19        | LRCK I2S audio      |                      |
|   20        | DIN I2S audio       |                      |
|   21        | DOUT I2S audio      |   unused             |
|   22        | Encoder Pin 1       |                      |
|   23        | Encoder Pin 2       |                      |
|   24        | Display: DC         |                      |
|   25        | Display: Reset      |                      |
|   26        | unused              |                      |
|   27        | Display: LED        |                      |

