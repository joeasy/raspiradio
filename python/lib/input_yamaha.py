#!/usr/bin/env python

import gaugette.rotary_encoder
import RPi.GPIO as GPIO
import spidev
from   evdev import InputDevice, categorize, ecodes, list_devices
import thread
import time
from   select import select
from   Adafruit_ADS1x15 import ADS1x15


A_PIN      = 3             # 1st pin of encoder
B_PIN      = 4             # 2nd pin of encoder
SWITCH_PIN = 7             # switch pin of encoder

ADS1115 = 0x01	           # 16-bit ADC

GPIO.setmode(GPIO.BOARD)   # RPi.GPIO Layout like pin Numbers on raspi

key_code = None

encoder = None

adc = ADS1x15(ic=ADS1115)  # Ananlog Digital Converter for front panel input

#-----------------------------------------------------------------#
#             set key code to enter                               #
#-----------------------------------------------------------------#
def switch_pressed(message):
    print message
    global key_code
    if message == 7:
        key_code = "KEY_ENTER"

#-----------------------------------------------------------------#
#             translate key code to string                        #
#-----------------------------------------------------------------#
def key_code_to_string(code):
    if code == 103: return "KEY_UP"
    if code == 108: return "KEY_DOWN"
    if code == 105: return "KEY_LEFT"
    if code == 106: return "KEY_RIGHT"
    if code == 28:  return "KEY_ENTER"
    if code == 139: return "KEY_MENU"
    if code == 164: return "KEY_PLAYPAUSE"

#-----------------------------------------------------------------#
#                 background thred to get keycode                 #
#-----------------------------------------------------------------#
def keypressd(lirc_device):
    global key_code
    event_type  = ""
    repeat_cout = 0
    for event in lirc_device.read_loop():
        if event.type == ecodes.EV_KEY:
            #print(str(event))
            string = str(event)
            if "val 01" in string: event_type = "DOWN"
            if "val 02" in string: event_type = "REPEAT"
            if "val 00" in string: event_type = "UP"
            if event_type == "DOWN":
                key_code = key_code_to_string(event.code)
            if event_type == "REPEAT":
                repeat_cout = repeat_cout +1
                if repeat_cout > 4:
                    key_code = key_code_to_string(event.code)
            if event_type == "UP":
                if repeat_cout > 4:
                    key_code = None
                repeat_cout = 0

#-----------------------------------------------------------------#
#                       read encoder                              #
#-----------------------------------------------------------------#
def readLeftRight(min_value, max_value, current_value, ir_value):
    delta = 0
    enc_delta = 0
    new_value = current_value
    if ir_value == "KEY_LEFT":
        delta = - 1
    if ir_value == "KEY_RIGHT":
        delta = + 1
    enc_delta = int(encoder.get_delta() / 4)
    if (delta != 0 or enc_delta !=0 ):
    	new_value = current_value + delta + enc_delta
    	if (new_value > max_value):
        	new_value = max_value
    	if (new_value < min_value):
        	new_value = min_value
    return new_value

#-----------------------------------------------------------------#
#                       read lirc socket                          #
#-----------------------------------------------------------------#
def read_key():
    global key_code
    result = ""
    if key_code != None:
        result = key_code
        key_code = None
    return result

#-----------------------------------------------------------------#
#                       read encoder                              #
#-----------------------------------------------------------------#
#def readEncoder(min_encoder_value, max_encoder_value, current_value):
#    delta = int(encoder.get_delta() / 4)
#    new_value = current_value
#    if (delta != 0):
#    	new_value = current_value + delta
#    	if (new_value > max_encoder_value):
#        	new_value = max_encoder_value
#    	if (new_value < min_encoder_value):
#        	new_value= min_encoder_value
#    return new_value

#----------------------------------------------------------------#
#    Function to read SPI data from MCP3008 chip                 #
#    Channel must be an integer 0-7                              #
#----------------------------------------------------------------#
def ReadChannel(channel):
    data = 0
    for x in range(0, 3):
        adc = spi.xfer2([1,(8+channel)<<4,0])
        data = data + ((adc[1]&3) << 8) + adc[2]
    data = int(data/3)
    return data

#----------------------------------------------------------------#
#    Function to read Yamaha front panel buttond with adc        #
#----------------------------------------------------------------#
def Read_Yamaha_Front_Panel_Buttons(channel):
    # Select the gain and sample speed
    gain = 4096  # +/- 4.096V
    sps  = 860   # 860 samples per second
    button = ""
    volts = adc.readADCSingleEnded(channel, gain, sps) / 1000
    if channel == 0:
        if volts > 2.9:
            button = ""
        elif volts < 0.2:
            button = "KEY_RDS"
        elif volts > 0.4 and volts < 0.8:
            button = "KEY_MODE"
        elif volts > 0.9 and volts < 1.2:
            button = "KEY_START"
        elif volts > 1.3 and volts < 1.6:
            button = "KEY_EON"
        elif volts > 1.8 and volts < 2.1:
            button = "KEY_FM"
    elif channel == 1:
        if volts > 3:
            button = ""
        elif volts < 0.2:
            button = "KEY_MEMORY"
        elif volts > 0.4 and volts < 0.9:
            button = "KEY_EDIT"
        elif volts > 1.1 and volts < 1.6:
            button = "KEY_ABC"
        elif volts > 1.7 and volts < 2.1:
            button = "KEY_1"
        elif volts > 2.2 and volts < 2.6:
            button = "KEY_2"
    elif channel == 2:
        if volts > 3:
            button = ""
        elif volts < 0.2:
            button = "KEY_3"
        elif volts > 0.4 and volts < 0.8:
            button = "KEY_4"
        elif volts > 0.9 and volts < 1.3:
            button = "KEY_5"
        elif volts > 1.4 and volts < 1.7:
            button = "KEY_6"
        elif volts > 1.9 and volts < 2.1:
            button = "KEY_7"
        elif volts > 2.2 and volts < 2.6:
            button = "KEY_8"
    return button

#-----------------------------------------------------------------#
#          background thred to get front panel keys               #
#-----------------------------------------------------------------#
def Read_Panel():
    global key_code
    panel_key = Read_Yamaha_Front_Panel_Buttons(0)
    if panel_key != "":
        key_code = panel_key
        print "Panel: " + panel_key
    panel_key = Read_Yamaha_Front_Panel_Buttons(1)
    if panel_key != "":
        key_code = panel_key
        print "Panel: " + panel_key
    panel_key = Read_Yamaha_Front_Panel_Buttons(2)
    if panel_key != "":
        key_code = panel_key
        print "Panel: " + panel_key

#-----------------------------------------------------------------#
#                      start some things                          #
#-----------------------------------------------------------------#
def init():
    global encoder
    lirc_device = InputDevice('/dev/input/event0')
    print(lirc_device)
    # define rotary encoder and start background thread
    encoder = gaugette.rotary_encoder.RotaryEncoder.Worker(A_PIN, B_PIN)
    encoder.start()
    GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(SWITCH_PIN, GPIO.FALLING, callback=switch_pressed, bouncetime=300)
    thread.start_new_thread(keypressd, (lirc_device, ))
    thread.start_new_thread(Read_Panel, ())
