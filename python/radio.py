#!/usr/local/bin/python
#!/usr/bin/env python

import time
from   lib import libmpdfunctions as mpd
from   lib import libpt2322 as audio
from   lib import tft as display
import gaugette.rotary_encoder
import RPi.GPIO as GPIO
import spidev
from   datetime import datetime
from   random import randint
import re
import json
import iwlib
from evdev import InputDevice, categorize, ecodes, list_devices
import thread
from select import select

mpd.init()
audio.init()

start_time = datetime.now() # remember time when script was started

A_PIN = 3                   # 1st pin of encoder
B_PIN = 4                   # 2nd pin of encoder
SWITCH_PIN = 7             # switch pin of encoder

GPIO.setmode(GPIO.BOARD)    # RPi.GPIO Layout like pin Numbers on raspi

#display.ini() # init the display

lirc_device = InputDevice('/dev/input/event0')
print(lirc_device)
lirc_code = None

# define rotary encoder and start background thread
encoder = gaugette.rotary_encoder.RotaryEncoder.Worker(A_PIN, B_PIN)
encoder.start()

class update_intervall:
    wifi             = 1000
    radio            = 1000
    tone             = 50
    time             = 500
    tone_adjust_idle = 5000
    tone_update      = 50
    tone_switch      = 1000
    disp_update      = 10
    source_switch    = 1000
    play_pause       = 300

class last_update:
    wifi             = 0
    radio            = 0
    tone             = 0
    tone_adjust_idle = 0
    tone_update      = 0
    time             = 0
    tone_switch      = 0
    disp_update      = 0
    source_switch    = 0
    play_pause       = 0

# define the tone modes
class tone_mode:
    volume = 0
    bass   = 1
    mid    = 2
    treble = 3
    mute   = 4

tones        = [0,0,0,0,0]                     # bass, mid, treble, volume
prev_tones   = [0,0,0,0,0]                            # the last values
tone_strings = ["Vol", "Bass", "Mid", "Treb"] # Stings in the display fore tones

num_sources     = 1 # number of input sources
num_tone_modes           = 3    # number of tone adjustment modes
num_radio_channels       = 8    # number of radio channels

class sources:
    IRadio = 0
    Airpay = 1

source_strings = ["RAD", "AIR"]

class states:
    current_channel   = 0
    current_tone_mode = tone_mode.volume
    current_source    = sources.IRadio
    mode_changed      = True


# restore saved values from disk
with open('config.sav') as data_file:
    tones = json.load(data_file)

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
    global lirc_code
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
                lirc_code = key_code_to_string(event.code)
            if event_type == "REPEAT":
                repeat_cout = repeat_cout +1
                if repeat_cout > 4:
                    lirc_code = key_code_to_string(event.code)
            if event_type == "UP":
                if repeat_cout > 4:
                    lirc_code = None
                repeat_cout = 0

#-----------------------------------------------------------------#
#  is like arduino map function                                   #
#  scales a value within a given range to another range           #
#-----------------------------------------------------------------#
def amap(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

#-----------------------------------------------------------------#
# returns the elapsed milliseconds since the start of the program #
#-----------------------------------------------------------------#
def millis():
   dt = datetime.now() - start_time
   ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
   return int(ms)

# get current wifi signal level
def get_wifi(timestamp):
    if display.test_mode:
        display.disp_elements.wifi = randint(0,100)
        return
    if (timestamp - last_update.wifi > update_intervall.wifi):
        wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
        display.disp_content.wifi = wifi_stat['stats']['level']
        last_update.wifi = timestamp

#-----------------------------------------------------------------#
#     switch radio channels                                       #
#-----------------------------------------------------------------#
def switch_channel(ir_value):
    if ir_value == "KEY_UP":
        if states.current_channel != num_radio_channels:
            states.current_channel = states.current_channel + 1
        else:
            states.current_channel = 0
        mpd.play(states.current_channel)
    if ir_value == "KEY_DOWN":
        if states.current_channel != 0:
            states.current_channel = states.current_channel - 1
        else:
            states.current_channel = num_radio_channels
        mpd.play(states.current_channel)

#-----------------------------------------------------------------#
#     switch input source                                         #
#-----------------------------------------------------------------#
def switch_source(timestamp):
    if (timestamp - last_update.source_switch > update_intervall.source_switch):
        states.current_source = states.current_source + 1
        if states.current_source > num_sources:
            states.current_source = 0
        disp_content.source = source_strings[states.current_source]
        last_update.source_switch = now

#-----------------------------------------------------------------#
#     switch application mode - is triggert by push button        #
#-----------------------------------------------------------------#
def switch_tone(message):
    last_tone_adjusted = millis()
    if (millis() - last_update.tone_switch > update_intervall.tone_switch):
        states.mode_changed = True
        states.current_tone_mode = states.current_tone_mode + 1
        if (states.current_tone_mode > num_tone_modes):
            states.current_tone_mode = 0

#-----------------------------------------------------------------#
#     react on playpause key                                      #
#-----------------------------------------------------------------#
def play_pause(timestamp):
    if (timestamp - last_update.play_pause > update_intervall.play_pause):
        if mpd.stat() == "play":
            mpd.stop()
        else:
            mpd.play(states.current_channel)


#-----------------------------------------------------------------#
#  update tones if they were changed and save the state to file   #
#-----------------------------------------------------------------#
def update_tones():
    changed = False
    if (tones[tone_mode.volume] !=prev_tones[tone_mode.volume]):
        audio.masterVolume(tones[tone_mode.volume])
        prev_tones[tone_mode.volume] = tones[tone_mode.volume]
        display.disp_content.volume = tones[tone_mode.volume]
        if tones[tone_mode.volume] == 0:
            audio.muteOn()
        else:
            audio.muteOff()
        changed = True
    elif (tones[tone_mode.bass] !=prev_tones[tone_mode.bass]):
        audio.bass(tones[tone_mode.bass])
        prev_tones[tone_mode.bass] = tones[tone_mode.bass]
        changed = True
    elif (tones[tone_mode.mid] !=prev_tones[tone_mode.mid]):
        audio.middle(tones[tone_mode.mid])
        prev_tones[tone_mode.mid] = tones[tone_mode.mid]
        changed = True
    elif (tones[tone_mode.treble] !=prev_tones[tone_mode.treble]):
        audio.treble(tones[tone_mode.treble])
        prev_tones[tone_mode.treble] = tones[tone_mode.treble]
        changed = True
    if changed:
        with open('config.sav', 'w') as outfile:
            json.dump(tones, outfile)

#-----------------------------------------------------------------#
#     app mode to adjust volume meds and trebble                  #
#-----------------------------------------------------------------#
def tone_adjust(ir_value):
    global tones
    value = readIR(0, 100, tones[states.current_tone_mode], ir_value)
    #value = readEncoder(0, 100, tones[states.current_tone_mode])
    if (value != tones[states.current_tone_mode]):
        tones[states.current_tone_mode] = value
        if (states.current_tone_mode != tone_mode.volume):
            last_update.tone_adjust_idle = millis()
    value = readEncoder(0, 100, tones[states.current_tone_mode])
    if (value != tones[states.current_tone_mode]):
        tones[states.current_tone_mode] = value
        if (states.current_tone_mode != tone_mode.volume):
            last_update.tone_adjust_idle = millis()

    #value = readEncoder(0, 100, tones[states.current_tone_mode])

#-----------------------------------------------------------------#
#                       read encoder                              #
#-----------------------------------------------------------------#
def readIR(min_value, max_value, current_value, ir_value):
    delta = 0
    new_value = current_value
    if ir_value == "KEY_LEFT":
        delta = -1
    if ir_value == "KEY_RIGHT":
        delta = 1
    if (delta != 0):
    	new_value = current_value + delta
    	if (new_value > max_value):
        	new_value = max_value
    	if (new_value < min_value):
        	new_value = min_value
    return new_value

#-----------------------------------------------------------------#
#                       read lirc socket                          #
#-----------------------------------------------------------------#
def read_lirc():
    global lirc_code
    result = ""
    if lirc_code != None:
        result = lirc_code
        lirc_code = None
    return result

#-----------------------------------------------------------------#
#                       read encoder                              #
#-----------------------------------------------------------------#
def readEncoder(min_encoder_value, max_encoder_value, current_value):
    delta = int(encoder.get_delta() / 4)
    new_value = current_value
    if (delta != 0):
    	new_value = current_value + delta
    	if (new_value > max_encoder_value):
        	new_value = max_encoder_value
    	if (new_value < min_encoder_value):
        	new_value= min_encoder_value
    return new_value

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

def get_mpt_info(timestamp):
    if (timestamp - last_update.radio > update_intervall.radio):    # update radio data
        if mpd.stat() == "play":
            (name, artist, title) = mpd.info()
            display.disp_content.mpd_stat = "play"
            display.disp_content.name     = name
            display.disp_content.artist   = artist
            display.disp_content.title    = title
        else:
            display.disp_content.mpd_stat = "stop"
            display.disp_content.name     = ""
            display.disp_content.artist   = ""
            display.disp_content.title    = ""
        last_update.radio                 = timestamp

#-----------------------------------------------------------------#
#           main programm loop                                    #
#-----------------------------------------------------------------#
def loop():

    now = millis()              # get timestamp
    ir_value = read_lirc()      # read IR
    switch_channel(ir_value)    # change radio channel
    tone_adjust(ir_value)       # call tone adjust

    if ir_value == "KEY_ENTER":    # switch tone mode
        switch_tone(True)

    if (now - last_update.time > update_intervall.time):       # update time in diaplay
        display.disp_content.time = time.strftime("%H:%M")
        last_update.time = now

    if (now - last_update.tone > update_intervall.tone ): # update tones
        update_tones()
        last_update.tone = now
    if (now - last_update.tone_adjust_idle > update_intervall.tone_adjust_idle ): # switch back to volume after timeout
        mode_changed = True
        last_update.tone_adjust_idle = now
        states.current_tone_mode = tone_mode.volume

    get_mpt_info(now)

    if ir_value == "KEY_MENU":
        switch_source(now)

    if ir_value == "KEY_PLAYPAUSE":
        play_pause(now)

    display.disp_content.tonemode  = tone_strings[states.current_tone_mode]
    display.disp_content.tonevalue = tones[states.current_tone_mode]

    get_wifi(now)

    if (now - last_update.disp_update > update_intervall.disp_update):    # update display
        display.update_display(now)
        last_update.disp_update = now

#-----------------------------------------------------------------#
#              main program                                       #
#-----------------------------------------------------------------#
update_tones()
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(SWITCH_PIN, GPIO.FALLING, callback=switch_tone, bouncetime=300)
thread.start_new_thread(keypressd, (lirc_device, ))

mpd.play(3)
mpd.stop()
mpd.play(0)
audio.muteOff()
while True:
    time.sleep(0.03)
    loop()
