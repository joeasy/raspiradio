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
import os.path

controls.init()
mpd.init()
audio.init()
manager = Manager()

start_time = datetime.now()     # remember time when script was started

# how often (ms) sertain things are updated
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
    panel_buttons    = 100

# timestamp when somthing was updated last
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
    panel_buttons    = 0

# define the tone modes
class tone_mode:
    volume  = 0
    bass    = 1
    mid     = 2
    treble  = 3

tone_strings = ["Vol", "Bass", "Mid", "Treb"] # Stings in the display fore tones

num_app_modes      = 3   # application modes
num_tone_modes     = 3   # number of tone adjustment modes
num_radio_channels = 8   # number of radio channels

# operation modes of software
class app_modes:
    IRadio  = 0
    Airplay = 1
    Spotify = 2
    AUX     = 3

tone_mode_to_string = ["volume", "bass", "mid", "treble"]

app_states  = {
                "volume"    : 0,
                "bass"      : 0,
                "mid"       : 0,
                "treble"    : 0,
                "mute"      : 0,
                "input"     : 0,
                "channel"   : 0,
                "play"      : 0,
                "app_mode"  : 0,
                "tone_mode" : 0,
                "changed"   : True
              }

prev_app_states  = {
                "volume"    : 0,
                "bass"      : 0,
                "mid"       : 0,
                "treble"    : 0,
                "mute"      : 0,
                "input"     : 0,
                "channel"   : 0,
                "play"      : 0,
                "app_mode"  : 0,
                "tone_mode" : 0,
                "changed"   : True
              }

# which audio unput is active on which mode of the software
app_mode_to_input = [0,0,0,1]

app_mode_strings = ["RAD", "AIR", "SPOT", "AUX"]

# define systemd services which should run in which app mode
app_services = {
    app_modes.IRadio:  ['mpd'],
    app_modes.Airplay: ['shairport'],
    app_modes.Spotify: ['spotify-connect'],
    app_modes.AUX: ['']}

#-----------------------------------------------------------------#
#      restore settings from disk                                 #
#-----------------------------------------------------------------#
def restore_tones_old():
    global tones
    with open('config.sav') as data_file:
        tones = json.load(data_file)
    states.current_channel  = tones[tone_mode.channel]
    states.current_app_mode = tones[tone_mode.mode]
    audio.switch_input(tones[tone_mode.inp])

#-----------------------------------------------------------------#
#      restore settings from disk                                 #
#-----------------------------------------------------------------#
def restore_tones():
    global app_states
    global prev_app_states
    if os.path.exists('appstates.sav'):
        print("restoring states")
        with open('appstates.sav') as data_file:
            app_states = json.load(data_file)
    audio.switch_input(app_states["input"])

#-----------------------------------------------------------------#
#      turn on and off systemd unit acording to app mode          #
#-----------------------------------------------------------------#
def unit_control(current_app):
    for group in app_services:
        for cservice in  app_services[group]:
            if cservice != '':
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

#-----------------------------------------------------------------#
#               get current wifi signal level                     #
#-----------------------------------------------------------------#
def get_wifi(timestamp):
    if (timestamp - last_update.wifi > update_intervall.wifi):
        wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
        display.disp_content.wifi = wifi_stat['stats']['quality']
        last_update.wifi = timestamp

#-----------------------------------------------------------------#
#              switch radio channels                              #
#-----------------------------------------------------------------#
def switch_channel(key_value):
    changed = False
    if key_value == "KEY_UP":
        if app_states["channel"] != num_radio_channels:
            app_states["channel"] = app_states["channel"] + 1
        else:
            app_states["channel"] = 0
        changed = True
    elif key_value == "KEY_DOWN":
        if app_states["channel"] != 0:
            app_states["channel"] = app_states["channel"] - 1
        else:
            app_states["channel"] = num_radio_channels
        changed = True
    if re.search("KEY_[0-9]+", key_value):
        regex = re.search("KEY_([0-9]+)", key_value)
        app_states["channel"] = int(regex.group(1)) - 1
        changed = True
    if changed:
        mpd.play(app_states["channel"])

#-----------------------------------------------------------------#
#              switch input source                                #
#-----------------------------------------------------------------#
def switch_source(timestamp):
    if (timestamp - last_update.app_mode > update_intervall.app_mode):
        app_states["app_mode"] = app_states["app_mode"] + 1
        if app_states["app_mode"] > num_app_modes:
            app_states["app_mode"] = 0
        display.disp_content.app_mode = app_mode_strings[app_states["app_mode"]]
        unit_control(app_states["app_mode"])
        app_states["input"]  = app_mode_to_input[app_states["app_mode"]]
        last_update.app_mode  = timestamp

#-----------------------------------------------------------------#
#     switch application mode - is triggert by push button        #
#-----------------------------------------------------------------#
def switch_tone(timestamp):
    last_tone_adjusted = timestamp
    if (timestamp - last_update.tone_switch > update_intervall.tone_switch):
        app_states["changed"] = True
        app_states["tone_mode"] = app_states["tone_mode"] + 1
        if (app_states["tone_mode"] > num_tone_modes):
            app_states["tone_mode"] = 0
        if (app_states["tone_mode"] != tone_mode.volume):
            last_update.tone_adjust_idle = timestamp

#-----------------------------------------------------------------#
#              react on playpause key                             #
#-----------------------------------------------------------------#
def play_pause(timestamp):
    if (timestamp - last_update.play_pause > update_intervall.play_pause):
        if app_states["play"] == 1:
            app_states["play"] = 0
        else:
            app_states["play"] = 1

#-----------------------------------------------------------------#
#  update tones if they were changed and save the state to file   #
#-----------------------------------------------------------------#
def update_tones():
    changed = False
    if (app_states["volume"] !=prev_app_states["volume"]):
        audio.masterVolume(app_states["volume"])
        prev_app_states["volume"] = app_states["volume"]
        display.disp_content.volume = app_states["volume"]
        if app_states["volume"] == 0:
            audio.muteOn()
        else:
            audio.muteOff()
        app_states["changed"] = True
    if (app_states["bass"] !=prev_app_states["bass"]):
        audio.bass(app_states["bass"])
        prev_app_states["bass"] = app_states["bass"]
        app_states["changed"] = True
    if (app_states["mid"] !=prev_app_states["mid"]):
        audio.middle(app_states["mid"])
        prev_app_states["mid"] = app_states["mid"]
        app_states["changed"] = True
    if (app_states["treble"] !=prev_app_states["treble"]):
        audio.treble(app_states["treble"])
        prev_app_states["treble"] = app_states["treble"]
        app_states["changed"] = True
    if (app_states["input"] != prev_app_states["input"]):
        audio.switch_input(app_states["input"])
        prev_app_states["input"] = app_states["input"]
        app_states["changed"] = True
    if (app_states["tone_mode"] != prev_app_states["tone_mode"]):
        prev_app_states["tone_mode"] = app_states["tone_mode"]
        app_states["changed"] = True
    if (app_states["channel"] != prev_app_states["channel"]):
        mpd.play(app_states["channel"])
        prev_app_states["channel"] = app_states["channel"]
        app_states["changed"] = True
    if (app_states["play"] != prev_app_states["play"]):
        if app_states["play"] == 0:
            mpd.stop()
        else:
            mpd.play(app_states["channel"])
        prev_app_states["play"] = app_states["play"]
        app_states["changed"] = True
    if app_states["changed"]:
        with open('appstates.sav', 'w') as outfile:
            json.dump(app_states, outfile)

#-----------------------------------------------------------------#
#     app mode to adjust volume meds and trebble                  #
#-----------------------------------------------------------------#
def tone_adjust(key_value):
    global tones
    value = controls.readLeftRight(0, 100, app_states[tone_mode_to_string[app_states["tone_mode"]]], key_value)
    if value != app_states[tone_mode_to_string[app_states["tone_mode"]]]:
        app_states[tone_mode_to_string[app_states["tone_mode"]]] = value
        if (app_states["tone_mode"] != tone_mode.volume):
            last_update.tone_adjust_idle = millis()

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
    if (app_states["play"] == 1 and mpd.stat() != "play"):
        mpd.play(app_states["channel"])
    if key_value == "KEY_PLAYPAUSE":
        play_pause(now)

#-----------------------------------------------------------------#
#           main programm loop                                    #
#-----------------------------------------------------------------#
def loop():
    now = millis()                  # get timestamp
    key_value = controls.read_key() # read controls
    if (now - last_update.panel_buttons > update_intervall.panel_buttons):
        button = controls.Read_Panel()
        if button != "":
            key_value = button
            time.sleep(0.2)

    if key_value != None and key_value != "":
        print "Control Key: " + key_value

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
        app_states["tone_mode"] = tone_mode.volume

    if key_value == "KEY_MENU":
        switch_source(now)

    display.disp_content.tonemode  = tone_strings[app_states["tone_mode"]]
    display.disp_content.tonevalue = app_states[tone_mode_to_string[app_states["tone_mode"]]]

    get_wifi(now)

    if app_states["app_mode"] == app_modes.IRadio:
        radio_loop(now,key_value)
    else:
        if mpd.stat() == "play":
            mpd.stop()

    if (now - last_update.disp_update > update_intervall.disp_update):    # update display
        display.update_display(now)
        last_update.disp_update = now

#-----------------------------------------------------------------#
#              main program                                       #
#-----------------------------------------------------------------#
#time.sleep(1)
restore_tones()
update_tones()
display.disp_content.app_mode = app_mode_strings[app_states["app_mode"]]
unit_control(app_states["app_mode"])
if app_states["play"] == 0:
    mpd.stop()
else:
    mpd.play(app_states["channel"])

while True:
    time.sleep(0.03)
    loop()
