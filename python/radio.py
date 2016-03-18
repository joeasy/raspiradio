#!/usr/local/bin/python
#!/usr/bin/env python

import pygame
from   pygame.locals import *
import time
import os
from   lib import libmpdfunctions as mpd
from   lib import libpt2322 as audio
import gaugette.rotary_encoder
import RPi.GPIO as GPIO
import spidev
from   datetime import datetime
from   random import randint
import re
import json
import lirc

pygame.font.init()
mpd.init()
audio.init()

start_time = datetime.now() # remember time when script was started

A_PIN = 3                   # 1st pin of encoder
B_PIN = 4                   # 2nd pin of encoder
SWITCH_PIN = 7             # switch pin of encoder

GPIO.setmode(GPIO.BOARD)    # RPi.GPIO Layout like pin Numbers on raspi

# define rotary encoder and start background thread
encoder = gaugette.rotary_encoder.RotaryEncoder.Worker(A_PIN, B_PIN)
encoder.start()

sockid=lirc.init("appleremote", blocking = False)  # connect ti linux lircd


# get screen dimensions
if os.path.exists("/sys/class/graphics/fb1/virtual_size"):
    with open('/sys/class/graphics/fb1/virtual_size') as file:
        lines = file.readlines()
    lines[0] = lines[0].strip()
    parts = re.split(',', lines[0])
    size_x = int(parts[0])
    size_y = int(parts[1])
    print("found screen: " + str(size_x) + "x" + str(size_y))
    os.environ["SDL_FBDEV"] = "/dev/fb1"
    import iwlib
    test_mode = False

else:
    print("running in test mode ...")
    size_x = 320
    size_y = 240
    test_mode = True

screen = pygame.display.set_mode((size_x,size_y))
pygame.init()
pygame.mouse.set_visible(False)

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

# define the tone modes
class tone_mode:
    volume = 0
    bass   = 1
    mid    = 2
    treble = 3
    mute   = 4

tones        = [100,100,40,100,0]                     # bass, mid, treble, volume
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

# define display areas
class disp_content:
    tonemode  = ""
    tonevalue = ""
    time      = ""
    name      = ""
    artist    = ""
    title     = ""
    source    = ""

# restore saved values from disk
with open('config.sav') as data_file:
    tones = json.load(data_file)

# define colors
white      = (255,255,255)
black      = (0,0,0)
light_gray = (200,200,200)
dark_gray  = (150,150,150)
red        = (255,0,0)

# define fonts
small_font      = pygame.font.Font("fonts/NotoSans-Regular.ttf", int(size_y/9.14))
small_font_bold = pygame.font.Font("fonts/NotoSans-Bold.ttf", int(size_y/9.14))
medium_font     = pygame.font.Font("fonts/NotoSans-Regular.ttf", int(size_y/7.11))
large_font      = pygame.font.Font("fonts/NotoSans-Regular.ttf", int(size_y/5.33))
bold_font       = pygame.font.Font("fonts/NotoSans-Bold.ttf", int(size_y/7.11))
icon_font_small = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", int(size_y/8))
icon_font_large = pygame.font.Font("fonts/Material-Design-Iconic-Font.ttf", int(size_y/2.28))

# render icons
wifi_icon_high   = icon_font_small.render(u'\uf2e8',True,black)
wifi_icon_medium = icon_font_small.render(u'\uf2e2',True,black)
wifi_icon_low    = icon_font_small.render(u'\uf2e7',True,red)
vol_icon_high    = icon_font_small.render(u'\uf3bc',True,black)
vol_icon_medium  = icon_font_small.render(u'\uf3b9',True,black)
vol_icon_low     = icon_font_small.render(u'\uf3ba',True,black)
vol_icon_off     = icon_font_small.render(u'\uf3bb',True,red)
play_icon        = icon_font_small.render(u'\uf3aa',True,black)
pause_icon       = icon_font_small.render(u'\uf3a7',True,red)
radio_icon       = icon_font_large.render(u'\uf2c2',True,black)
airplay_icon     = icon_font_large.render(u'\uf3d2',True,black)
bluetooth_icon   = icon_font_large.render(u'\uf282',True,black)
tone_icon        = icon_font_large.render(u'\uf10f',True,black)

class disp_elements:
    name   = ""
    artist = ""
    title  = ""
    tone   = "treble"
    wifi   = 0
    vol    = 0

class scroll_pos:
    name   = 0
    artist = 0
    title  = 0

class disp_positions:
    statusbar_pos       = int(size_y/4.27)
    wifi_icon_x         = int(size_x/1.3)
    wifi_text_x         = int(size_x/1.13)
    vol_icon_x          = int(size_x/40)
    time_text_x         = int(size_x/2.46)
    play_icon_x         = int(size_x/8)
    name_y              = int(size_y/2.67)
    artist_y            = int(size_y/1.94)
    title_y             = int(size_y/1.52)
    radio_icon_x        = int(size_x/2.91)
    tone_icon_x         = int(size_x/5)
    big_icon_y          = int(size_y/2.84)
    tone_text_x         = int(size_x/2.3)
    tone_text_y         = int(size_y/2.3)
    current_tone_text_x = int(size_x/5)

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

# scroll text if longer that display width
def scroll_text(raw_text,font,y_pos,x_pos,speed):
    text = font.render(raw_text, True, black)
    if ( size_x < text.get_width() ):
        text = font.render(raw_text + " * ", True, black)
        x_pos = x_pos - speed
        if x_pos < -text.get_width():
            x_pos=0
        screen.blit(text,(x_pos,y_pos))
        screen.blit(text, (x_pos+text.get_width(),y_pos))
        return x_pos
    else:
        text = font.render(raw_text, True, black)
        x_pos = (size_x - text.get_width()) // 2
        screen.blit(text,(x_pos,y_pos))
        return 0

# print progress bar 0 - 100
def print_bar(value):
    bar_width = int(value * size_x/1.14/100)
    x_start   = int(size_x/16)
    y_start   = int(size_y/1.16)
    x_width   = int(size_x/1.14)
    y_width   = int(size_y/12.8)
    pygame.draw.rect(screen, black, (x_start - 2, y_start - 2, x_width + 4, y_width + 4))
    pygame.draw.rect(screen, light_gray, (x_start, y_start, x_width, y_width))
    pygame.draw.rect(screen, dark_gray, (x_start, y_start, bar_width, y_width))

# get current wifi signal level
def get_wifi():
    if test_mode:
        disp_elements.wifi = randint(0,100)
        return
    wifi_stat = iwlib.iwconfig.get_iwconfig("wlan0")
    disp_elements.wifi = str(wifi_stat['stats']['level'])

# wifi signal display
def show_wifi(timestamp):
    if (timestamp - last_update.wifi > update_intervall.wifi):    # update radio data
        get_wifi()
        last_update.wifi = timestamp
    if disp_elements.wifi > 66:
        screen.blit(wifi_icon_high,(disp_positions.wifi_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.wifi > 33:
        screen.blit(wifi_icon_medium,(disp_positions.wifi_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.wifi <= 33:
        screen.blit(wifi_icon_low,(disp_positions.wifi_icon_x,disp_positions.statusbar_pos))
    wifi_text = small_font.render(str(disp_elements.wifi), True, black)
    screen.blit(wifi_text,(disp_positions.wifi_text_x,disp_positions.statusbar_pos))
    wifi_text = small_font.render(str(disp_elements.wifi), True, black)
    screen.blit(wifi_text,(disp_positions.wifi_text_x,disp_positions.statusbar_pos))

# volume icon and bar
def show_vol(timestamp):
    vol_value = tones[tone_mode.volume]
    if (timestamp - last_update.tone > update_intervall.tone):    # update radio data
        #disp_elements.vol = randint(0,100)
        last_update.tone = timestamp
    if vol_value == 0:
        screen.blit(vol_icon_off,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif vol_value > 66:
        screen.blit(vol_icon_high,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif vol_value > 33:
        screen.blit(vol_icon_medium,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif vol_value <= 33:
        screen.blit(vol_icon_low,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    print_bar(tones[states.current_tone_mode])
    current_tone_text = small_font.render(tone_strings[states.current_tone_mode], True, black)
    screen.blit(current_tone_text,(disp_positions.current_tone_text_x,disp_positions.statusbar_pos))

# time display update
def show_time():
    time_text = small_font_bold.render(disp_content.time, True, black)
    screen.blit(time_text,(disp_positions.time_text_x,disp_positions.statusbar_pos))

# mpd infos
def show_mpd(timestamp):
    if mpd.stat() == "play":
        screen.blit(play_icon,(disp_positions.play_icon_x,disp_positions.statusbar_pos))
        scroll_pos.name   = scroll_text(disp_content.name,medium_font,disp_positions.name_y,scroll_pos.name,1)
        scroll_pos.artist = scroll_text(disp_content.artist,medium_font,disp_positions.artist_y,scroll_pos.artist,1)
        scroll_pos.title  = scroll_text(disp_content.title,bold_font,disp_positions.title_y,scroll_pos.title,1)
    else:
        screen.blit(pause_icon,(disp_positions.play_icon_x,disp_positions.statusbar_pos))
        screen.blit(radio_icon,(disp_positions.radio_icon_x,disp_positions.big_icon_y))

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
            states.current_channel = current_channel - 1
        else:
            states.current_channel = num_radio_channels
        mpd.play(states.current_channel)

#-----------------------------------------------------------------#
#     switch input source                                         #
#-----------------------------------------------------------------#
def switch_source():
    states.current_source = states.current_source + 1
    if states.current_source > num_sources:
        states.current_source = 0
    disp_content.source = source_strings[states.current_source]

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
#  update tones if they were changed and save the state to file   #
#-----------------------------------------------------------------#
def update_tones():
    changed = False
    if (tones[tone_mode.volume] !=prev_tones[tone_mode.volume]):
        audio.masterVolume(tones[tone_mode.volume])
        prev_tones[tone_mode.volume] = tones[tone_mode.volume]
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
    result = ""
    codeIR = lirc.nextcode()
    if codeIR != []:
        result = codeIR[0]
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

#-----------------------------------------------------------------#
#  update display if nesesarry                                    #
#-----------------------------------------------------------------#
def update_display(now):
    screen.fill(white)
    #screen.blit(tone_icon,(disp_positions.tone_icon_x,disp_positions.big_icon_y))
    #tone_text = large_font.render(disp_elements.tone, True, black)
    #screen.blit(tone_text,(disp_positions.tone_text_x,disp_positions.tone_text_y))

    show_wifi(now)
    show_vol(now)
    show_time()
    show_mpd(now)

    pygame.display.update()

#-----------------------------------------------------------------#
#           main programm loop                                    #
#-----------------------------------------------------------------#
def loop():

    now = millis()              # get timestamp
    ir_value = read_lirc()      # read IR
    switch_channel(ir_value)    # change radio channel
    tone_adjust(ir_value)       # call tone adjust

    if ir_value == "KEY_OK":    # switch tone mode
        switch_tone(True)

    if (now - last_update.time > update_intervall.time):       # update time in diaplay
        disp_content.time = time.strftime("%H:%M")
        last_update.time = now

    if (now - last_update.tone > update_intervall.tone ): # update tones
        update_tones()
        last_update.tone = now
    if (now - last_update.tone_adjust_idle > update_intervall.tone_adjust_idle ): # switch back to volume after timeout
        mode_changed = True
        last_update.tone_adjust_idle = now
        states.current_tone_mode = tone_mode.volume

    if (now - last_update.radio > update_intervall.radio):    # update radio data
        (name, artist, title) = mpd.info()
        disp_content.name     = name
        disp_content.artist   = artist
        disp_content.title    = title
        last_update.radio     = now

    if ir_value == "KEY_MENU":
        if (now - last_update.source_switch > update_intervall.source_switch):    # update source
            switch_source()
            last_update.source_switch = now

    disp_content.tonemode  = tone_strings[states.current_tone_mode]
    disp_content.tonevalue = str(tones[states.current_tone_mode])

    if (now - last_update.disp_update > update_intervall.disp_update):    # update display
        update_display(now)
        last_update.disp_update = now

#-----------------------------------------------------------------#
#              main program                                       #
#-----------------------------------------------------------------#
last_tone_adjusted = millis();
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(SWITCH_PIN, GPIO.FALLING, callback=switch_tone, bouncetime=300)
while True:
    time.sleep(0.02)
    loop()



# main loop
#while True:
#    now = millis()
#    screen.fill(white)
#    screen.blit(tone_icon,(disp_positions.tone_icon_x,disp_positions.big_icon_y))
#    tone_text = large_font.render(disp_elements.tone, True, black)
#    screen.blit(tone_text,(disp_positions.tone_text_x,disp_positions.tone_text_y))


#    show_wifi(now)
#    show_vol(now)
#    show_time()
    #show_mpd(now)




#    pygame.display.update()
#    time.sleep(0.05)
