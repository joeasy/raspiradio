#!/usr/bin/env python

import time
from   lib import input_yamaha as controls
from   lib import libmpdfunctions as mpd
from   lib import libpt2322 as audio
from   lib import tft as display
from   datetime import datetime
from   random import randint
import re
import json
import iwlib
from   systemd.manager import Manager

controls.init()
mpd.init()
audio.init()
manager = Manager()

start_time = datetime.now() # remember time when script was started

class update_intervall:
    wifi             = 1000
    radio            = 1000
    tone             = 50
    time             = 500
    tone_adjust_idle = 5000
    tone_update      = 50
    tone_switch      = 1000
    disp_update      = 10
    app_mode         = 1000
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
    app_mode         = 0
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

num_app_modes            = 1    # application modes
num_tone_modes           = 3    # number of tone adjustment modes
num_radio_channels       = 8    # number of radio channels

class app_modes:
    IRadio = 0
    Airplay = 1

app_mode_strings = ["RAD", "AIR"]

class states:
    current_channel   = 0
    current_tone_mode = tone_mode.volume
    mode_changed      = True
    current_app_mode  = app_modes.IRadio

# define services which should run in which app mode
app_services = {
    app_modes.IRadio:  ['mpd'],
    app_modes.Airplay: ['shairport']}

# restore saved values from disk
with open('config.sav') as data_file:
    tones = json.load(data_file)

#-----------------------------------------------------------------#
#      turn on and off systemd unit acording to app mode          #
#-----------------------------------------------------------------#
def unit_control(current_app):
    for group in app_services:
        for cservice in  app_services[group]:
            unit_name = cservice + ".service"
            unit = manager.get_unit(unit_name)
            current_state = unit.properties.ActiveState
            if (current_app == group):
                if current_state == 'inactive':
                    print("starting " + cservice)
                    try:
                        unit.start('fail')
                    except:
                        print"unable to start " + cservice
            else:
                if current_state == 'active':
                    print("stopping " + cservice)
                    try:
                        unit.stop('fail')
                    except:
                        print"unable to stop " + cservice

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
def switch_channel(key_value):
    if key_value == "KEY_UP":
        if states.current_channel != num_radio_channels:
            states.current_channel = states.current_channel + 1
        else:
            states.current_channel = 0
        mpd.play(states.current_channel)
    if key_value == "KEY_DOWN":
        if states.current_channel != 0:
            states.current_channel = states.current_channel - 1
        else:
            states.current_channel = num_radio_channels
        mpd.play(states.current_channel)

#-----------------------------------------------------------------#
#     switch input source                                         #
#-----------------------------------------------------------------#
def switch_source(timestamp):
    if (timestamp - last_update.app_mode > update_intervall.app_mode):
        states.current_app_mode = states.current_app_mode + 1
        if states.current_app_mode > num_app_modes:
            states.current_app_mode = 0
        display.disp_content.app_mode = app_mode_strings[states.current_app_mode]
        unit_control(states.current_app_mode)
        last_update.app_mode = timestamp

#-----------------------------------------------------------------#
#     switch application mode - is triggert by push button        #
#-----------------------------------------------------------------#
def switch_tone(timestamp):
    last_tone_adjusted = timestamp
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
def tone_adjust(key_value):
    global tones
    value = controls.readLeftRight(0, 100, tones[states.current_tone_mode], key_value)
    #value = readEncoder(0, 100, tones[states.current_tone_mode])
    if (value != tones[states.current_tone_mode]):
        tones[states.current_tone_mode] = value
        if (states.current_tone_mode != tone_mode.volume):
            last_update.tone_adjust_idle = millis()
    #value = controls.readEncoder(0, 100, tones[states.current_tone_mode])
    #if (value != tones[states.current_tone_mode]):
    #    tones[states.current_tone_mode] = value
    #    if (states.current_tone_mode != tone_mode.volume):
    #        last_update.tone_adjust_idle = millis()

#-----------------------------------------------------------------#
#                get data from mpd                                #
#-----------------------------------------------------------------#
def get_mpd_info(timestamp):
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
#       do the special thing in radio mode                        #
#-----------------------------------------------------------------#
def radio_loop(now,key_value):
    switch_channel(key_value)    # change radio channel
    get_mpd_info(now)
    if key_value == "KEY_PLAYPAUSE":
        play_pause(now)

#-----------------------------------------------------------------#
#           main programm loop                                    #
#-----------------------------------------------------------------#
def loop():

    now = millis()                  # get timestamp
    key_value = controls.read_key() # read IR
    tone_adjust(key_value)           # call tone adjust

    if key_value == "KEY_ENTER":    # switch tone mode
        switch_tone(now)

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

    if key_value == "KEY_MENU":
        switch_source(now)

    display.disp_content.tonemode  = tone_strings[states.current_tone_mode]
    display.disp_content.tonevalue = tones[states.current_tone_mode]

    get_wifi(now)

    if states.current_app_mode == app_modes.IRadio: radio_loop(now,key_value)

    if (now - last_update.disp_update > update_intervall.disp_update):    # update display
        display.update_display(now)
        last_update.disp_update = now

#-----------------------------------------------------------------#
#              main program                                       #
#-----------------------------------------------------------------#
update_tones()
display.disp_content.app_mode = app_mode_strings[states.current_app_mode]
unit_control(states.current_app_mode)
mpd.play(1)
time.sleep(1)
mpd.stop()

while True:
    time.sleep(0.03)
    loop()
