#!/usr/local/bin/python
#!/usr/bin/env python

import pygame
from pygame.locals import *
import time
import os
from lib import libmpdfunctions as mpd
from datetime import datetime
from random import randint
import re

pygame.font.init()
mpd.init()

start_time = datetime.now() # remember time when script was started


# get screen dimensions
if os.path.exists("/sys/class/graphics/fb1/virtual_size"):
    with open('/sys/class/graphics/fb1/virtual_size') as file:
        lines = file.readlines()
    lines[0] = lines[0].strip()
    parts = re.split(',', lines[0])
    size_x = int(parts[0])
    size_y = int(parts[1])
    print("found screen: " + size_x + "x" + size_y)
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

wifi_update_intervall = 1000
mpd_update_intervall  = 1000
vol_update_intervall  = 2000

class last_update:
    wifi = 0
    mpd  = 0
    vol  = 0

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
    wifi   = 0
    vol    = 0

class scroll_pos:
    name   = 0
    artist = 0
    title  = 0

class disp_positions:
    statusbar_pos = int(size_y/4.27)
    wifi_icon_x   = int(size_x/1.3)
    wifi_text_x   = int(size_x/1.13)
    vol_icon_x    = int(size_x/40)
    time_text_x   = int(size_x/2.46)
    play_icon_x   = int(size_x/8)
    name_y        = int(size_y/2.67)
    artist_y      = int(size_y/1.94)
    title_y       = int(size_y/1.52)
    radio_icon_x  = int(size_x/2.91)
    radio_icon_y  = int(size_y/2.84)

# get milliseconds since program start
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
    if (timestamp - last_update.wifi > wifi_update_intervall):    # update radio data
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
    if (timestamp - last_update.vol > vol_update_intervall):    # update radio data
        disp_elements.vol = randint(0,100)
        last_update.vol = timestamp
    if disp_elements.vol == 0:
        screen.blit(vol_icon_off,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.vol > 66:
        screen.blit(vol_icon_high,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.vol > 33:
        screen.blit(vol_icon_medium,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    elif disp_elements.vol <= 33:
        screen.blit(vol_icon_low,(disp_positions.vol_icon_x,disp_positions.statusbar_pos))
    print_bar(disp_elements.vol)

# time display update
def show_time():
    time_str=time.strftime("%H:%M")
    time_text = small_font_bold.render(time_str, True, black)
    screen.blit(time_text,(disp_positions.time_text_x,disp_positions.statusbar_pos))

# mpd infos
def show_mpd(timestamp):
    if mpd.stat() == "play":
        if (timestamp - last_update.mpd > mpd_update_intervall):    # update radio data
            (disp_elements.name, disp_elements.artist, disp_elements.title) = mpd.info()
            last_update.mpd = timestamp
        screen.blit(play_icon,(disp_positions.play_icon_x,disp_positions.statusbar_pos))
        scroll_pos.name   = scroll_text(disp_elements.name,medium_font,disp_positions.name_y,scroll_pos.name,1)
        scroll_pos.artist = scroll_text(disp_elements.artist,medium_font,disp_positions.artist_y,scroll_pos.artist,1)
        scroll_pos.title  = scroll_text(disp_elements.title,bold_font,disp_positions.title_y,scroll_pos.title,2)
    else:
        screen.blit(pause_icon,(disp_positions.play_icon_x,disp_positions.statusbar_pos))
        screen.blit(radio_icon,(disp_positions.radio_icon_x,disp_positions.radio_icon_y))

# main loop
while True:
    now = millis()
    screen.fill(white)

    show_wifi(now)
    show_vol(now)
    show_time()
    show_mpd(now)

    pygame.display.update()
    time.sleep(0.02)
